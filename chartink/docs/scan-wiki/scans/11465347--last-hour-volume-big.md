---
scan_id: 11465347
scan_name: Last hour volume big
source_url: https://chartink.com/screener/last-hour-volume-big
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Moving average","Momentum"]
tags: ["universe:futures","indicator:volume","indicator:sma","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 3
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# Last hour volume big

## Source

- Chartink URL: https://chartink.com/screener/last-hour-volume-big
- Scan ID: `11465347`
- Slug: `last-hour-volume-big`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-04-11T12:02:18.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11465347.json](../source-snapshots/11465347.json)
- Text snapshot: [source-snapshots/11465347.txt](../source-snapshots/11465347.txt)

## What this scan is for

This is a **intraday** screen over **futures** with **1** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Moving average, Momentum**.

The active tests, in captured order:
- [7] 60 minute volume + [6] 60 minute volume crossed below [-7] 60 minute sma( close ,  20 ) * 0.25

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Last hour volume big
Scan id: 11465347
Slug: last-hour-volume-big
Source URL: https://chartink.com/screener/last-hour-volume-big
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-11T12:02:18.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [7] 60 minute volume + [6] 60 minute volume crossed above [-7] 60 minute sma( close ,  20 ) * 2
2. [Enabled] [7] 60 minute volume + [6] 60 minute volume crossed below [-7] 60 minute sma( close ,  20 ) * 0.25
3. [Disabled] [7] 60 minute obv + [6] 60 minute obv - [5] 60 minute obv - [5] 60 minute obv crossed above [-7] 60 minute sma( close ,  20 ) * 200
4. [Disabled] [7] 60 minute obv + [6] 60 minute obv - [5] 60 minute obv - [5] 60 minute obv crossed below [-7] 60 minute sma( close ,  20 ) * 200

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( [=7] 1 hour volume + [=6] 1 hour volume < [-7] 1 hour sma( [=7] 1 hour volume + [=6] 1 hour volume , 20 ) * 0.25 and [ =6 ] 1 hour volume + [ =5 ] 1 hour volume >= [ -8 ] 1 hour sma( [=7] 1 hour volume + [=6] 1 hour volume , 20 )* 0.25 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | [7] 60 minute volume + [6] 60 minute volume crossed above [-7] 60 minute sma( close ,  20 ) * 2 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 2 | Enabled | root | [7] 60 minute volume + [6] 60 minute volume crossed below [-7] 60 minute sma( close ,  20 ) * 0.25 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 3 | Disabled | root | [7] 60 minute obv + [6] 60 minute obv - [5] 60 minute obv - [5] 60 minute obv crossed above [-7] 60 minute sma( close ,  20 ) * 200 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 4 | Disabled | root | [7] 60 minute obv + [6] 60 minute obv - [5] 60 minute obv - [5] 60 minute obv crossed below [-7] 60 minute sma( close ,  20 ) * 200 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[7] 60 minute volume + [6] 60 minute volume crossed below [-7] 60 minute sma( close ,  20 ) * 0.25` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **3** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `[7] 60 minute volume + [6] 60 minute volume crossed above [-7] 60 minute sma( close ,  20 ) * 2`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `[7] 60 minute obv + [6] 60 minute obv - [5] 60 minute obv - [5] 60 minute obv crossed above [-7] 60 minute sma( close ,  20 ) * 200`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `[7] 60 minute obv + [6] 60 minute obv - [5] 60 minute obv - [5] 60 minute obv crossed below [-7] 60 minute sma( close ,  20 ) * 200`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `obv` — appears 16 time(s) in the expression tree
- `volume` — appears 8 time(s) in the expression tree
- `sma` — appears 4 time(s) in the expression tree

### Operators observed
- `+` — 4 occurrence(s)
- `*` — 4 occurrence(s)
- `-` — 4 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `crossed below` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Moving average, Momentum, Multi-factor.
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
- Retains **3** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Volume/delivery, Moving average, Momentum
- **Tags:** universe:futures, indicator:volume, indicator:sma, timeframe:intraday-bars, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

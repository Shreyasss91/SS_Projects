---
scan_id: 14250010
scan_name: rsi blackwolf money movement_PriceAction
source_url: https://chartink.com/screener/rsi-blackwolf-money-movement
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volume/delivery", "Trend following", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "universe:futures", "indicator:volume", "indicator:ema", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Moving average
---

# rsi blackwolf money movement_PriceAction

## Source

- Chartink URL: https://chartink.com/screener/rsi-blackwolf-money-movement
- Scan ID: `14250010`
- Slug: `rsi-blackwolf-money-movement`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-12-18T01:50:30.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14250010.json](../source-snapshots/14250010.json)
- Text snapshot: [source-snapshots/14250010.txt](../source-snapshots/14250010.txt)

## What this scan is for

This is a **intraday** screen over **futures** with **1** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Trend following, Momentum, Multi-factor**.
The active tests, in captured order, are:
- [0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) crossed above 5000000

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: rsi blackwolf money movement_PriceAction
Scan id: 14250010
Slug: rsi-blackwolf-money-movement
Source URL: https://chartink.com/screener/rsi-blackwolf-money-movement
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-18T01:50:30.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [0] 15 minute ema( close ,  15 ) - [0] 15 minute ema( close ,  15 ) crossed above [-1] 15 minute max( 450 ,  [0] 15 minute ema( close ,  15 ) - [0] 15 minute ema( close ,  15 ) )
2. [Disabled] [0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) crossed above [-1] 15 minute max( 315 ,  [0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) )
3. [Enabled] [0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) crossed above 5000000

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( [0] 15 minute ema( greatest(  ( [0] 15 minute close - [-1] 15 minute close ) * [0] 15 minute volume, 0  ) , 45 ) - [0] 15 minute ema( greatest(  ( [-1] 15 minute close - [0] 15 minute close ) * [0] 15 minute volume, 0  ) , 45 ) > 5000000 and [ -1 ] 15 minute ema( greatest(  ( [0] 15 minute close - [-1] 15 minute close ) * [0] 15 minute volume, 0  ) , 45 )- [ -1 ] 15 minute ema( greatest(  ( [-1] 15 minute close - [0] 15 minute close ) * [0] 15 minute volume, 0  ) , 45 )<= 5000000 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | [0] 15 minute ema( close ,  15 ) - [0] 15 minute ema( close ,  15 ) crossed above [-1] 15 minute max( 450 ,  [0] 15 minute ema( close ,  15 ) - [0] 15 minute ema( close ,  15 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 2 | Disabled | root | [0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) crossed above [-1] 15 minute max( 315 ,  [0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 3 | Enabled | root | [0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) crossed above 5000000 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). EMA is an exponentially weighted moving average of the chosen field. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `[0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) crossed above 5000000` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). EMA is an exponentially weighted moving average of the chosen field. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `[0] 15 minute ema( close ,  15 ) - [0] 15 minute ema( close ,  15 ) crossed above [-1] 15 minute max( 450 ,  [0] 15 minute ema( close ,  15 ) - [0] 15 minute ema( close ,  15 ) )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `[0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) crossed above [-1] 15 minute max( 315 ,  [0] 15 minute ema( close ,  45 ) - [0] 15 minute ema( close ,  45 ) )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 20 time(s) in the expression tree
- `ema` — appears 10 time(s) in the expression tree
- `greatest` — appears 10 time(s) in the expression tree
- `volume` — appears 10 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree

### Operators observed
- `*` — 10 occurrence(s)
- `-` — 3 occurrence(s)
- `crossed above` — 3 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery, Trend following, Momentum, Multi-factor.
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
- **Methods:** Moving average, Volume/delivery, Trend following, Momentum, Multi-factor
- **Tags:** bias:upward-condition, universe:futures, indicator:volume, indicator:ema, timeframe:daily, timeframe:intraday-bars
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

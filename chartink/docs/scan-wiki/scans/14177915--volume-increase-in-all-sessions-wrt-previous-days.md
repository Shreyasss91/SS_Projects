---
scan_id: 14177915
scan_name: VOLUME INCREASE IN ALL SESSIONS WRT PREVIOUS DAYS
source_url: https://chartink.com/screener/volume-increase-in-all-sessions-wrt-previous-days
market: Indian equities
horizon: Intraday
classification: ["Volume/delivery", "Momentum"]
tags: ["universe:futures", "indicator:volume", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 3
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# VOLUME INCREASE IN ALL SESSIONS WRT PREVIOUS DAYS

## Source

- Chartink URL: https://chartink.com/screener/volume-increase-in-all-sessions-wrt-previous-days
- Scan ID: `14177915`
- Slug: `volume-increase-in-all-sessions-wrt-previous-days`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-12-13T00:59:22.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14177915.json](../source-snapshots/14177915.json)
- Text snapshot: [source-snapshots/14177915.txt](../source-snapshots/14177915.txt)

## What this scan is for

This scan, titled "VOLUME INCREASE IN ALL SESSIONS WRT PREVIOUS DAYS", appears designed to screen Indian equities in the **futures** universe using **1 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 30_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: VOLUME INCREASE IN ALL SESSIONS WRT PREVIOUS DAYS
Scan id: 14177915
Slug: volume-increase-in-all-sessions-wrt-previous-days
Source URL: https://chartink.com/screener/volume-increase-in-all-sessions-wrt-previous-days
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-13T00:59:22.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [0] 30 minute volume / [-13] 30 minute volume crossed above 50
2. [Disabled] [0] 30 minute sum( close ,  13 ) crossed above [-1] 30 minute max( 78 ,  [0] 30 minute sum( close ,  13 ) )
3. [Disabled] [0] 30 minute sum( close ,  13 ) crossed above 150
4. [Enabled] [0] 30 minute max( 13 ,  [0] 30 minute sum( close ,  13 ) ) / [0] 30 minute min( 13 ,  [0] 30 minute sum( close ,  13 ) ) crossed above 3

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( [0] 30 minute max( 13 , [0] 30 minute sum( [0] 30 minute volume / [-13] 30 minute volume , 13 ) ) / [0] 30 minute min( 13 , [0] 30 minute sum( [0] 30 minute volume / [-13] 30 minute volume , 13 ) ) > 3 and [ -1 ] 30 minute max( 13 , [0] 30 minute sum( [0] 30 minute volume / [-13] 30 minute volume , 13 ) )/ [ -1 ] 30 minute min( 13 , [0] 30 minute sum( [0] 30 minute volume / [-13] 30 minute volume , 13 ) )<= 3 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [0] 30 minute volume / [-13] 30 minute volume crossed above 50 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | Disabled | [0] 30 minute sum( close ,  13 ) crossed above [-1] 30 minute max( 78 ,  [0] 30 minute sum( close ,  13 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | Disabled | [0] 30 minute sum( close ,  13 ) crossed above 150 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | Enabled | [0] 30 minute max( 13 ,  [0] 30 minute sum( close ,  13 ) ) / [0] 30 minute min( 13 ,  [0] 30 minute sum( close ,  13 ) ) crossed above 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#4** `[0] 30 minute max( 13 ,  [0] 30 minute sum( close ,  13 ) ) / [0] 30 minute min( 13 ,  [0] 30 minute sum( close ,  13 ) ) crossed above 3` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **3** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `[0] 30 minute volume / [-13] 30 minute volume crossed above 50`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `[0] 30 minute sum( close ,  13 ) crossed above [-1] 30 minute max( 78 ,  [0] 30 minute sum( close ,  13 ) )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `[0] 30 minute sum( close ,  13 ) crossed above 150`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `volume` — appears 12 time(s) in the expression tree
- `sum` — appears 5 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 4 occurrence(s)
- `/` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `30_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
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
- **Methods:** Volume/delivery, Momentum
- **Tags:** universe:futures, indicator:volume, timeframe:intraday-bars, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

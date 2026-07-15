---
scan_id: 14370905
scan_name: buying interest at eod.. bullish for tomorrow
source_url: https://chartink.com/screener/buying-interest-at-eod-bullish-for-tomorrow
market: Indian equities
horizon: "Intraday"
classification: ["Other"]
tags: ["universe:nifty-200","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 5
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Other
---

# buying interest at eod.. bullish for tomorrow

## Source

- Chartink URL: https://chartink.com/screener/buying-interest-at-eod-bullish-for-tomorrow
- Scan ID: `14370905`
- Slug: `buying-interest-at-eod-bullish-for-tomorrow`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-12-27T01:29:53.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14370905.json](../source-snapshots/14370905.json)
- Text snapshot: [source-snapshots/14370905.txt](../source-snapshots/14370905.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **2** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Other**.

The active tests, in captured order:
- [6] 5 minute sum( close ,  6 ) > 50
- [6] 5 minute sum( close ,  6 ) > [-75] 5 minute sum( close ,  6 )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: buying interest at eod.. bullish for tomorrow
Scan id: 14370905
Slug: buying-interest-at-eod-bullish-for-tomorrow
Source URL: https://chartink.com/screener/buying-interest-at-eod-bullish-for-tomorrow
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-27T01:29:53.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [0] 15 minute buyer initiated trades ratio crossed above [-1] 15 minute max( 20 ,  [0] 15 minute buyer initiated trades ratio )
2. [Disabled] [0] 5 minute count( 75, 1 where [0] 5 minute buyer initiated trades ratio > 10 ) crossed above 4
3. [Disabled] [0] 5 minute buyer initiated trades ratio crossed above 20
4. [Disabled] [75] 5 minute buy orders quantity ratio crossed above 20
5. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] [6] 5 minute sum( close ,  6 ) > 50
    group_path: root/group[cash|all]
7. [Enabled] [6] 5 minute sum( close ,  6 ) > [-75] 5 minute sum( close ,  6 )
    group_path: root/group[cash|all]
8. [Disabled] [0] 15 minute max( 25 ,  [0] 15 minute sma( close ,  20 ) ) / [0] 15 minute min( 25 ,  [0] 15 minute sma( close ,  20 ) ) crossed above 5

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( [=6] 5 minute sum( [0] 5 minute "buy orders quantity / sell orders quantity" , 6 ) > 50 and [=6] 5 minute sum( [0] 5 minute "buy orders quantity / sell orders quantity" , 6 ) > [=-75] 5 minute sum( [0] 5 minute "buy orders quantity / sell orders quantity" , 6 ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | [0] 15 minute buyer initiated trades ratio crossed above [-1] 15 minute max( 20 ,  [0] 15 minute buyer initiated trades ratio ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 2 | Disabled | root | [0] 5 minute count( 75, 1 where [0] 5 minute buyer initiated trades ratio > 10 ) crossed above 4 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 3 | Disabled | root | [0] 5 minute buyer initiated trades ratio crossed above 20 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 4 | Disabled | root | [75] 5 minute buy orders quantity ratio crossed above 20 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 6 | Enabled | root/group[cash\|all] | [6] 5 minute sum( close ,  6 ) > 50 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 7 | Enabled | root/group[cash\|all] | [6] 5 minute sum( close ,  6 ) > [-75] 5 minute sum( close ,  6 ) | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 8 | Disabled | root | [0] 15 minute max( 25 ,  [0] 15 minute sma( close ,  20 ) ) / [0] 15 minute min( 25 ,  [0] 15 minute sma( close ,  20 ) ) crossed above 5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#6** `[6] 5 minute sum( close ,  6 ) > 50` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[6] 5 minute sum( close ,  6 ) > [-75] 5 minute sum( close ,  6 )` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **5** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `[0] 15 minute buyer initiated trades ratio crossed above [-1] 15 minute max( 20 ,  [0] 15 minute buyer initiated trades ratio )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `[0] 5 minute count( 75, 1 where [0] 5 minute buyer initiated trades ratio > 10 ) crossed above 4`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `[0] 5 minute buyer initiated trades ratio crossed above 20`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `[75] 5 minute buy orders quantity ratio crossed above 20`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `[0] 15 minute max( 25 ,  [0] 15 minute sma( close ,  20 ) ) / [0] 15 minute min( 25 ,  [0] 15 minute sma( close ,  20 ) ) crossed above 5`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `buyer initiated trades ratio` — appears 6 time(s) in the expression tree
- `buy orders quantity ratio` — appears 4 time(s) in the expression tree
- `sum` — appears 3 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 5 occurrence(s)
- `>` — 3 occurrence(s)
- `/` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `15_minute`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **5** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Other
- **Tags:** universe:nifty-200, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 14527084
scan_name: buy orders Daily TF
source_url: https://chartink.com/screener/buy-orders-daily-tf
market: Indian equities
horizon: "Intraday"
classification: ["Momentum"]
tags: ["universe:nifty-500","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Momentum
---

# buy orders Daily TF

## Source

- Chartink URL: https://chartink.com/screener/buy-orders-daily-tf
- Scan ID: `14527084`
- Slug: `buy-orders-daily-tf`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2024-01-06T11:10:16.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14527084.json](../source-snapshots/14527084.json)
- Text snapshot: [source-snapshots/14527084.txt](../source-snapshots/14527084.txt)

## What this scan is for

This is a **intraday** screen over **nifty 500** with **6** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Momentum**.

The active tests, in captured order:
- [0] 15 minute sum( close ,  25 ) crossed above 300
- [0] 5 minute sum( close ,  75 ) crossed above 1000
- [0] 15 minute sum( close ,  25 ) crossed above [-50] 15 minute max( 500 ,  [0] 15 minute sum( close ,  25 ) ) * 1.5
- [0] 5 minute sum( close ,  75 ) crossed above [-150] 5 minute max( 1500 ,  [0] 5 minute sum( close ,  75 ) ) * 1.5
- [0] 15 minute sum( close ,  25 ) crossed above [-50] 15 minute max( 500 ,  [0] 15 minute sum( close ,  25 ) ) * 3
- [0] 5 minute sum( close ,  75 ) crossed above [-150] 5 minute max( 1500 ,  [0] 5 minute sum( close ,  75 ) ) * 3

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: buy orders Daily TF
Scan id: 14527084
Slug: buy-orders-daily-tf
Source URL: https://chartink.com/screener/buy-orders-daily-tf
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2024-01-06T11:10:16.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily buy orders quantity ratio > 20
2. [Disabled] daily market cap / 10000000 < 5000
3. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
4. [Enabled] [0] 15 minute sum( close ,  25 ) crossed above 300
    group_path: root/group[cash|any]
5. [Enabled] [0] 5 minute sum( close ,  75 ) crossed above 1000
    group_path: root/group[cash|any]
6. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
7. [Enabled] [0] 15 minute sum( close ,  25 ) crossed above [-50] 15 minute max( 500 ,  [0] 15 minute sum( close ,  25 ) ) * 1.5
    group_path: root/group[cash|any]
8. [Enabled] [0] 5 minute sum( close ,  75 ) crossed above [-150] 5 minute max( 1500 ,  [0] 5 minute sum( close ,  75 ) ) * 1.5
    group_path: root/group[cash|any]
9. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
10. [Enabled] [0] 15 minute sum( close ,  25 ) crossed above [-50] 15 minute max( 500 ,  [0] 15 minute sum( close ,  25 ) ) * 3
    group_path: root/group[cash|any]
11. [Enabled] [0] 5 minute sum( close ,  75 ) crossed above [-150] 5 minute max( 1500 ,  [0] 5 minute sum( close ,  75 ) ) * 3
    group_path: root/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 500 ( ( cash ( [0] 15 minute sum( [0] 15 minute "buy orders quantity / sell orders quantity" , 25 ) > [-50] 15 minute max( 500 , [0] 15 minute sum( [0] 15 minute "buy orders quantity / sell orders quantity" , 25 ) ) * 3 and [ -1 ] 15 minute sum( [0] 15 minute "buy orders quantity / sell orders quantity" , 25 ) <= [ -51 ] 15 minute max( 500 , [0] 15 minute sum( [0] 15 minute "buy orders quantity / sell orders quantity" , 25 ) )* 3 or [0] 5 minute sum( [0] 5 minute "buy orders quantity / sell orders quantity" , 75 ) > [-150] 5 minute max( 1500 , [0] 5 minute sum( [0] 5 minute "buy orders quantity / sell orders quantity" , 75 ) ) * 3 and [ -1 ] 5 minute sum( [0] 5 minute "buy orders quantity / sell orders quantity" , 75 ) <= [ -151 ] 5 minute max( 1500 , [0] 5 minute sum( [0] 5 minute "buy orders quantity / sell orders quantity" , 75 ) )* 3 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily buy orders quantity ratio > 20 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 2 | 2 | Disabled | root | daily market cap / 10000000 < 5000 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Filters by market-capitalisation field from Chartink fundamentals. |
| 3 | 4 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  25 ) crossed above 300 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 5 | Enabled | root/group[cash\|any] | [0] 5 minute sum( close ,  75 ) crossed above 1000 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 7 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  25 ) crossed above [-50] 15 minute max( 500 ,  [0] 15 minute sum( close ,  25 ) ) * 1.5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 8 | Enabled | root/group[cash\|any] | [0] 5 minute sum( close ,  75 ) crossed above [-150] 5 minute max( 1500 ,  [0] 5 minute sum( close ,  75 ) ) * 1.5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 10 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  25 ) crossed above [-50] 15 minute max( 500 ,  [0] 15 minute sum( close ,  25 ) ) * 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 11 | Enabled | root/group[cash\|any] | [0] 5 minute sum( close ,  75 ) crossed above [-150] 5 minute max( 1500 ,  [0] 5 minute sum( close ,  75 ) ) * 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#4** `[0] 15 minute sum( close ,  25 ) crossed above 300` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[0] 5 minute sum( close ,  75 ) crossed above 1000` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[0] 15 minute sum( close ,  25 ) crossed above [-50] 15 minute max( 500 ,  [0] 15 minute sum( close ,  25 ) ) * 1.5` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[0] 5 minute sum( close ,  75 ) crossed above [-150] 5 minute max( 1500 ,  [0] 5 minute sum( close ,  75 ) ) * 1.5` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[0] 15 minute sum( close ,  25 ) crossed above [-50] 15 minute max( 500 ,  [0] 15 minute sum( close ,  25 ) ) * 3` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#11** `[0] 5 minute sum( close ,  75 ) crossed above [-150] 5 minute max( 1500 ,  [0] 5 minute sum( close ,  75 ) ) * 3` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily buy orders quantity ratio > 20`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `daily market cap / 10000000 < 5000`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Filters by market-capitalisation field from Chartink fundamentals.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `buy orders quantity ratio` — appears 11 time(s) in the expression tree
- `sum` — appears 10 time(s) in the expression tree
- `max` — appears 4 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 6 occurrence(s)
- `*` — 4 occurrence(s)
- `>` — 1 occurrence(s)
- `/` — 1 occurrence(s)
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
- Universe/segment: **nifty 500**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Momentum
- **Tags:** universe:nifty-500, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 14108100
scan_name: order book ratio increasing
source_url: https://chartink.com/screener/order-book-ratio-increasing
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volume/delivery", "Trend following", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "universe:futures", "indicator:sma", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 1
needs_review_filter_count: 0
root_segment: futures
root_join: any
primary_classification: Moving average
---

# order book ratio increasing

## Source

- Chartink URL: https://chartink.com/screener/order-book-ratio-increasing
- Scan ID: `14108100`
- Slug: `order-book-ratio-increasing`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-12-08T01:40:43.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14108100.json](../source-snapshots/14108100.json)
- Text snapshot: [source-snapshots/14108100.txt](../source-snapshots/14108100.txt)

## What this scan is for

This is a **intraday** screen over **futures** with **2** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Trend following, Momentum, Multi-factor**.
The active tests, in captured order, are:
- [0] 30 minute sma( close ,  20 ) crossed above [-6] 30 minute max( 150 ,  [0] 30 minute sma( close ,  20 ) ) * 1.8
- [0] 15 minute sma( close ,  20 ) crossed above [-6] 15 minute max( 150 ,  [0] 15 minute sma( close ,  20 ) ) * 1.8

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: order book ratio increasing
Scan id: 14108100
Slug: order-book-ratio-increasing
Source URL: https://chartink.com/screener/order-book-ratio-increasing
Root universe/segment: futures
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-08T01:40:43.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] 1 day ago close * 1 day ago volume > 100000000
2. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Enabled] [0] 30 minute sma( close ,  20 ) crossed above [-6] 30 minute max( 150 ,  [0] 30 minute sma( close ,  20 ) ) * 1.8
    group_path: root/group[cash|all]
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] [0] 15 minute sma( close ,  20 ) crossed above [-6] 15 minute max( 150 ,  [0] 15 minute sma( close ,  20 ) ) * 1.8
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( [0] 30 minute sma( [0] 30 minute "buy orders quantity / sell orders quantity" , 20 ) > [-6] 30 minute max( 150 , [0] 30 minute sma( [0] 30 minute "buy orders quantity / sell orders quantity" , 20 ) ) * 1.8 and [ -1 ] 30 minute sma( [0] 30 minute "buy orders quantity / sell orders quantity" , 20 )<= [ -7 ] 30 minute max( 150 , [0] 30 minute sma( [0] 30 minute "buy orders quantity / sell orders quantity" , 20 ) )* 1.8 ) ) or( cash ( [0] 15 minute sma( [0] 15 minute "buy orders quantity / sell orders quantity" , 20 ) > [-6] 15 minute max( 150 , [0] 15 minute sma( [0] 15 minute "buy orders quantity / sell orders quantity" , 20 ) ) * 1.8 and [ -1 ] 15 minute sma( [0] 15 minute "buy orders quantity / sell orders quantity" , 20 )<= [ -7 ] 15 minute max( 150 , [0] 15 minute sma( [0] 15 minute "buy orders quantity / sell orders quantity" , 20 ) )* 1.8 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | [0] 30 minute sma( close ,  20 ) crossed above [-6] 30 minute max( 150 ,  [0] 30 minute sma( close ,  20 ) ) * 1.8 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 5 | Enabled | root/group[cash\|all] | [0] 15 minute sma( close ,  20 ) crossed above [-6] 15 minute max( 150 ,  [0] 15 minute sma( close ,  20 ) ) * 1.8 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `[0] 30 minute sma( close ,  20 ) crossed above [-6] 30 minute max( 150 ,  [0] 30 minute sma( close ,  20 ) ) * 1.8` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[0] 15 minute sma( close ,  20 ) crossed above [-6] 15 minute max( 150 ,  [0] 15 minute sma( close ,  20 ) ) * 1.8` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **1** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `1 day ago close * 1 day ago volume > 100000000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `sma` — appears 4 time(s) in the expression tree
- `buy orders quantity ratio` — appears 4 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `*` — 3 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `>` — 1 occurrence(s)

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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_days_ago`, `30_minute`

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

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **1** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Moving average, Volume/delivery, Trend following, Momentum, Multi-factor
- **Tags:** bias:upward-condition, universe:futures, indicator:sma, timeframe:daily, timeframe:intraday-bars
- **Root universe:** futures
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

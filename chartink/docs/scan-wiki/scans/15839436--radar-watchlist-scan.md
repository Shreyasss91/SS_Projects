---
scan_id: 15839436
scan_name: Radar Watchlist Scan
source_url: https://chartink.com/screener/radar-watchlist-scan
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Moving average","Volatility"]
tags: ["universe:futures","indicator:volume","indicator:sma","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 7
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: futures
root_join: any
primary_classification: Volume/delivery
---

# Radar Watchlist Scan

## Source

- Chartink URL: https://chartink.com/screener/radar-watchlist-scan
- Scan ID: `15839436`
- Slug: `radar-watchlist-scan`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2024-04-11T16:03:21.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/15839436.json](../source-snapshots/15839436.json)
- Text snapshot: [source-snapshots/15839436.txt](../source-snapshots/15839436.txt)

## What this scan is for

This is a **intraday** screen over **futures** with **7** active leaf condition(s) under root join **any**.
Its method labels are derived only from active expressions: **Volume/delivery, Moving average, Volatility**.

The active tests, in captured order:
- daily open > 1 day ago close * 1.015
- daily open < 1 day ago close * 0.985
- daily volume > 1 day ago volume * 3
- daily volume > 1 day ago sma( close ,  3 ) * 3
- [0] 15 minute volume > [-1] 15 minute sma( close ,  3 ) * 10
- [0] 15 minute % change > [-1] 15 minute avg true range( 14 ) * 2
- ( [0] 15 minute high - [0] 15 minute low ) / [0] 15 minute close > [-1] 15 minute sma( close ,  14 ) * 4

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Radar Watchlist Scan
Scan id: 15839436
Slug: radar-watchlist-scan
Source URL: https://chartink.com/screener/radar-watchlist-scan
Root universe/segment: futures
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2024-04-11T16:03:21.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=futures join=any combination=passes measurevalue=default]  (path: root/group[futures|any])
2. [Enabled] daily open > 1 day ago close * 1.015
    group_path: root/group[futures|any]
3. [Enabled] daily open < 1 day ago close * 0.985
    group_path: root/group[futures|any]
4. [Disabled] [GROUP segment=futures join=any combination=passes measurevalue=default]  (path: root/group[futures|any])
5. [Enabled] daily volume > 1 day ago volume * 3
    group_path: root/group[futures|any]
6. [Enabled] daily volume > 1 day ago sma( close ,  3 ) * 3
    group_path: root/group[futures|any]
7. [Enabled] [0] 15 minute volume > [-1] 15 minute sma( close ,  3 ) * 10
    group_path: root/group[futures|any]
8. [Disabled] [GROUP segment=futures join=any combination=passes measurevalue=default]  (path: root/group[futures|any])
9. [Disabled] [0] 15 minute % change > 0.4
    group_path: root/group[futures|any]
10. [Disabled] ( [0] 15 minute high - [0] 15 minute low ) / [0] 15 minute close > 0.01
    group_path: root/group[futures|any]
11. [Enabled] [0] 15 minute % change > [-1] 15 minute avg true range( 14 ) * 2
    group_path: root/group[futures|any]
12. [Enabled] ( [0] 15 minute high - [0] 15 minute low ) / [0] 15 minute close > [-1] 15 minute sma( close ,  14 ) * 4
    group_path: root/group[futures|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( futures ( latest open > 1 day ago close * 1.015 or latest open < 1 day ago close * 0.985 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[futures\|any] | daily open > 1 day ago close * 1.015 | Inequality test: left expression must be strictly greater than right. |
| 2 | 3 | Enabled | root/group[futures\|any] | daily open < 1 day ago close * 0.985 | Inequality test: left expression must be strictly less than right. |
| 3 | 5 | Enabled | root/group[futures\|any] | daily volume > 1 day ago volume * 3 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 4 | 6 | Enabled | root/group[futures\|any] | daily volume > 1 day ago sma( close ,  3 ) * 3 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 5 | 7 | Enabled | root/group[futures\|any] | [0] 15 minute volume > [-1] 15 minute sma( close ,  3 ) * 10 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 9 | Disabled | root/group[futures\|any] | [0] 15 minute % change > 0.4 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 10 | Disabled | root/group[futures\|any] | ( [0] 15 minute high - [0] 15 minute low ) / [0] 15 minute close > 0.01 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 11 | Enabled | root/group[futures\|any] | [0] 15 minute % change > [-1] 15 minute avg true range( 14 ) * 2 | Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 12 | Enabled | root/group[futures\|any] | ( [0] 15 minute high - [0] 15 minute low ) / [0] 15 minute close > [-1] 15 minute sma( close ,  14 ) * 4 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **7** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily open > 1 day ago close * 1.015` — Inequality test: left expression must be strictly greater than right.
- **#3** `daily open < 1 day ago close * 0.985` — Inequality test: left expression must be strictly less than right.
- **#5** `daily volume > 1 day ago volume * 3` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#6** `daily volume > 1 day ago sma( close ,  3 ) * 3` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#7** `[0] 15 minute volume > [-1] 15 minute sma( close ,  3 ) * 10` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#11** `[0] 15 minute % change > [-1] 15 minute avg true range( 14 ) * 2` — Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#12** `( [0] 15 minute high - [0] 15 minute low ) / [0] 15 minute close > [-1] 15 minute sma( close ,  14 ) * 4` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #9
- **Condition (verbatim):** `[0] 15 minute % change > 0.4`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `( [0] 15 minute high - [0] 15 minute low ) / [0] 15 minute close > 0.01`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `volume` — appears 6 time(s) in the expression tree
- `close` — appears 5 time(s) in the expression tree
- `sma` — appears 3 time(s) in the expression tree
- `high` — appears 3 time(s) in the expression tree
- `low` — appears 3 time(s) in the expression tree
- `open` — appears 2 time(s) in the expression tree
- `% change` — appears 2 time(s) in the expression tree
- `avg true range` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 8 occurrence(s)
- `*` — 7 occurrence(s)
- `/` — 2 occurrence(s)
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
- Universe/segment: **futures**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volatility, Volume/delivery, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **7** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Volume/delivery, Moving average, Volatility
- **Tags:** universe:futures, indicator:volume, indicator:sma, timeframe:daily, timeframe:intraday-bars
- **Root universe:** futures
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

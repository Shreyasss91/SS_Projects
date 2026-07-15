---
scan_id: 4870241
scan_name: trade book
source_url: https://chartink.com/screener/trade-book-4
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volume/delivery"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "indicator:volume", "indicator:sma", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 14
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Moving average
---

# trade book

## Source

- Chartink URL: https://chartink.com/screener/trade-book-4
- Scan ID: `4870241`
- Slug: `trade-book-4`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-06-08T15:49:29.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4870241.json](../source-snapshots/4870241.json)
- Text snapshot: [source-snapshots/4870241.txt](../source-snapshots/4870241.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **5** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery**.
The active tests, in captured order, are:
- 1 day ago close * 1 day ago volume > 100000000
- [0] 15 minute buy orders quantity > [-1] 15 minute sma( close ,  400 ) * 8
- [0] 15 minute volume < [-1] 15 minute sma( close ,  48 ) * 4
- daily buy orders quantity ratio > 4
- [0] 30 minute sma( close ,  400 ) / [-4] 30 minute sma( close ,  400 ) > 1.4

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: trade book
Scan id: 4870241
Slug: trade-book-4
Source URL: https://chartink.com/screener/trade-book-4
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-08T15:49:29.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close * 1 day ago volume > 100000000
2. [Disabled] 1 day ago close * 1 day ago volume < 10000000000
3. [Disabled] [0] 15 minute buy orders quantity ratio > 3
4. [Disabled] [0] 15 minute buy orders ratio > 5
5. [Disabled] [0] 15 minute close crossed below [0] 15 minute buy orders vwap
6. [Disabled] [0] 15 minute buy orders vwap crossed above [0] 15 minute sell orders vwap
7. [Disabled] [0] 15 minute buy orders vwap crossed above [0] 15 minute sell orders vwap
8. [Disabled] [0] 15 minute volume > [0] 15 minute buyer initiated trades quantity * 10
9. [Disabled] [0] 30 minute buy orders quantity crossed above [-1] 30 minute sma( close ,  24 )
10. [Disabled] [0] 30 minute buy orders quantity ratio > 10
11. [Disabled] [0] 30 minute buy orders quantity > [-1] 30 minute sma( close ,  200 )
12. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
13. [Disabled] [0] 30 minute buy orders quantity > [-1] 30 minute sma( close ,  200 ) * 4
    group_path: root/group[cash|all]
14. [Disabled] [0] 30 minute volume < [-1] 30 minute sma( close ,  24 ) * 4
    group_path: root/group[cash|all]
15. [Enabled] [0] 15 minute buy orders quantity > [-1] 15 minute sma( close ,  400 ) * 8
    group_path: root/group[cash|all]
16. [Enabled] [0] 15 minute volume < [-1] 15 minute sma( close ,  48 ) * 4
    group_path: root/group[cash|all]
17. [Disabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|all])
18. [Enabled] daily buy orders quantity ratio > 4
    group_path: root/group[futures|all]
19. [Disabled] [0] 30 minute buy orders quantity ratio > 4
    group_path: root/group[futures|all]
20. [Disabled] [0] 15 minute buy orders quantity crossed above [-1] 15 minute max( 150 ,  [0] 15 minute buy orders quantity )
21. [Enabled] [0] 30 minute sma( close ,  400 ) / [-4] 30 minute sma( close ,  400 ) > 1.4

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 30 minute sma( [0] 30 minute buy orders quantity , 400 ) / [-4] 30 minute sma( [0] 30 minute buy orders quantity , 400 ) > 1.4 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 2 | Disabled | root | 1 day ago close * 1 day ago volume < 10000000000 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |
| 3 | 3 | Disabled | root | [0] 15 minute buy orders quantity ratio > 3 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 4 | Disabled | root | [0] 15 minute buy orders ratio > 5 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 5 | Disabled | root | [0] 15 minute close crossed below [0] 15 minute buy orders vwap | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. VWAP is volume-weighted average price for the session/period context Chartink supplies. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 6 | Disabled | root | [0] 15 minute buy orders vwap crossed above [0] 15 minute sell orders vwap | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. VWAP is volume-weighted average price for the session/period context Chartink supplies. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 7 | Disabled | root | [0] 15 minute buy orders vwap crossed above [0] 15 minute sell orders vwap | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. VWAP is volume-weighted average price for the session/period context Chartink supplies. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 8 | Disabled | root | [0] 15 minute volume > [0] 15 minute buyer initiated trades quantity * 10 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 9 | Disabled | root | [0] 30 minute buy orders quantity crossed above [-1] 30 minute sma( close ,  24 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 10 | Disabled | root | [0] 30 minute buy orders quantity ratio > 10 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 11 | Disabled | root | [0] 30 minute buy orders quantity > [-1] 30 minute sma( close ,  200 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 13 | Disabled | root/group[cash\|all] | [0] 30 minute buy orders quantity > [-1] 30 minute sma( close ,  200 ) * 4 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 14 | Disabled | root/group[cash\|all] | [0] 30 minute volume < [-1] 30 minute sma( close ,  24 ) * 4 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 15 | Enabled | root/group[cash\|all] | [0] 15 minute buy orders quantity > [-1] 15 minute sma( close ,  400 ) * 8 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 16 | Enabled | root/group[cash\|all] | [0] 15 minute volume < [-1] 15 minute sma( close ,  48 ) * 4 | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | 18 | Enabled | root/group[futures\|all] | daily buy orders quantity ratio > 4 | Inequality test: left expression must be strictly greater than right. |
| 17 | 19 | Disabled | root/group[futures\|all] | [0] 30 minute buy orders quantity ratio > 4 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 18 | 20 | Disabled | root | [0] 15 minute buy orders quantity crossed above [-1] 15 minute max( 150 ,  [0] 15 minute buy orders quantity ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 19 | 21 | Enabled | root | [0] 30 minute sma( close ,  400 ) / [-4] 30 minute sma( close ,  400 ) > 1.4 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#15** `[0] 15 minute buy orders quantity > [-1] 15 minute sma( close ,  400 ) * 8` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#16** `[0] 15 minute volume < [-1] 15 minute sma( close ,  48 ) * 4` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#18** `daily buy orders quantity ratio > 4` — Inequality test: left expression must be strictly greater than right.
- **#21** `[0] 30 minute sma( close ,  400 ) / [-4] 30 minute sma( close ,  400 ) > 1.4` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **14** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #2
- **Condition (verbatim):** `1 day ago close * 1 day ago volume < 10000000000`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `[0] 15 minute buy orders quantity ratio > 3`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `[0] 15 minute buy orders ratio > 5`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `[0] 15 minute close crossed below [0] 15 minute buy orders vwap`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. VWAP is volume-weighted average price for the session/period context Chartink supplies. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `[0] 15 minute buy orders vwap crossed above [0] 15 minute sell orders vwap`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. VWAP is volume-weighted average price for the session/period context Chartink supplies. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `[0] 15 minute buy orders vwap crossed above [0] 15 minute sell orders vwap`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. VWAP is volume-weighted average price for the session/period context Chartink supplies. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `[0] 15 minute volume > [0] 15 minute buyer initiated trades quantity * 10`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `[0] 30 minute buy orders quantity crossed above [-1] 30 minute sma( close ,  24 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `[0] 30 minute buy orders quantity ratio > 10`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `[0] 30 minute buy orders quantity > [-1] 30 minute sma( close ,  200 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #13
- **Condition (verbatim):** `[0] 30 minute buy orders quantity > [-1] 30 minute sma( close ,  200 ) * 4`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `[0] 30 minute volume < [-1] 30 minute sma( close ,  24 ) * 4`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #19
- **Condition (verbatim):** `[0] 30 minute buy orders quantity ratio > 4`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #20
- **Condition (verbatim):** `[0] 15 minute buy orders quantity crossed above [-1] 15 minute max( 150 ,  [0] 15 minute buy orders quantity )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `buy orders quantity` — appears 12 time(s) in the expression tree
- `sma` — appears 8 time(s) in the expression tree
- `volume` — appears 7 time(s) in the expression tree
- `buy orders quantity ratio` — appears 4 time(s) in the expression tree
- `close` — appears 3 time(s) in the expression tree
- `buy orders vwap` — appears 3 time(s) in the expression tree
- `sell orders vwap` — appears 2 time(s) in the expression tree
- `buy orders ratio` — appears 1 time(s) in the expression tree
- `buyer initiated trades quantity` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 11 occurrence(s)
- `*` — 7 occurrence(s)
- `crossed above` — 4 occurrence(s)
- `<` — 3 occurrence(s)
- `crossed below` — 1 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_days_ago`, `30_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **5** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **14** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Moving average, Volume/delivery
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, indicator:volume, indicator:sma, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

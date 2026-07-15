---
scan_id: 9162807
scan_name: overlapping DI+ and DI-
source_url: https://chartink.com/screener/overlapping-di-and-di
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Moving average","Momentum"]
tags: ["universe:cash","indicator:volume","indicator:sma","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 8
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# overlapping DI+ and DI-

## Source

- Chartink URL: https://chartink.com/screener/overlapping-di-and-di
- Scan ID: `9162807`
- Slug: `overlapping-di-and-di`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2022-07-29T17:05:43.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/9162807.json](../source-snapshots/9162807.json)
- Text snapshot: [source-snapshots/9162807.txt](../source-snapshots/9162807.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **4** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Moving average, Momentum**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- [0] 5 minute count( 320, 1 where [0] 5 minute dx_diff + 1.5 > 0 ) > 240
- [0] 5 minute count( 320, 1 where [0] 5 minute dx_diff + 1.5 < 3 ) crossed below 240
- [0] 5 minute sma( close ,  80 ) crossed below 0.05 * ( [0] 5 minute max( 1120 ,  [0] 5 minute sma( close ,  80 ) ) - [0] 5 minute min( 1120 ,  [0] 5 minute sma( close ,  80 ) ) )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: overlapping DI+ and DI-
Scan id: 9162807
Slug: overlapping-di-and-di
Source URL: https://chartink.com/screener/overlapping-di-and-di
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-07-29T17:05:43.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] 1 day ago close * 1 day ago volume > 100000000
2. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
4. [Disabled] [0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) > 0
    group_path: root/group[cash|all]
5. [Disabled] [0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) > [0] 5 minute max( 240 ,  [0] 5 minute dx_diff )
    group_path: root/group[cash|all]
6. [Disabled] [0] 5 minute dx_diff crossed above 0.9 * [0] 5 minute max( 650 ,  [0] 5 minute dx_diff )
    group_path: root/group[cash|all]
7. [Disabled] [0] 5 minute count( 650, 1 where [0] 5 minute dx_diff / [0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) crossed above 0.6 ) crossed above 2
    group_path: root/group[cash|all]
8. [Enabled] [0] 5 minute count( 320, 1 where [0] 5 minute dx_diff + 1.5 > 0 ) > 240
    group_path: root/group[cash|all]
9. [Enabled] [0] 5 minute count( 320, 1 where [0] 5 minute dx_diff + 1.5 < 3 ) crossed below 240
    group_path: root/group[cash|all]
10. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
11. [Disabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|any]
12. [Disabled] [0] 5 minute sma( close ,  156 ) crossed below 0.4
    group_path: root/group[cash|any]
13. [Enabled] [0] 5 minute sma( close ,  80 ) crossed below 0.05 * ( [0] 5 minute max( 1120 ,  [0] 5 minute sma( close ,  80 ) ) - [0] 5 minute min( 1120 ,  [0] 5 minute sma( close ,  80 ) ) )
    group_path: root/group[cash|any]
14. [Disabled] [0] 5 minute count( 100, 1 where daily abs( [0] 5 minute adx di positive( 250 ) - [0] 5 minute adx di negative( 250 ) ) > 0.4 ) = 0
    group_path: root/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 5 minute count( 320, 1 where [0] 5 minute "adx di positive( 250 ) -  adx di negative( 250 )" + 1.5 > 0 ) > 240 and [0] 5 minute count( 320, 1 where [0] 5 minute "adx di positive( 250 ) -  adx di negative( 250 )" + 1.5 < 3 ) < 240 and [ -1 ] 5 minute count( 320, 1 where [0] 5 minute "adx di positive( 250 ) -  adx di negative( 250 )" + 1.5 < 3 ) >= 240 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 3 | 4 | Disabled | root/group[cash\|all] | [0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) > 0 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 5 | Disabled | root/group[cash\|all] | [0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) > [0] 5 minute max( 240 ,  [0] 5 minute dx_diff ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 6 | Disabled | root/group[cash\|all] | [0] 5 minute dx_diff crossed above 0.9 * [0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 7 | Disabled | root/group[cash\|all] | [0] 5 minute count( 650, 1 where [0] 5 minute dx_diff / [0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) crossed above 0.6 ) crossed above 2 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 8 | Enabled | root/group[cash\|all] | [0] 5 minute count( 320, 1 where [0] 5 minute dx_diff + 1.5 > 0 ) > 240 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 9 | Enabled | root/group[cash\|all] | [0] 5 minute count( 320, 1 where [0] 5 minute dx_diff + 1.5 < 3 ) crossed below 240 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 11 | Disabled | root/group[cash\|any] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |
| 10 | 12 | Disabled | root/group[cash\|any] | [0] 5 minute sma( close ,  156 ) crossed below 0.4 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 13 | Enabled | root/group[cash\|any] | [0] 5 minute sma( close ,  80 ) crossed below 0.05 * ( [0] 5 minute max( 1120 ,  [0] 5 minute sma( close ,  80 ) ) - [0] 5 minute min( 1120 ,  [0] 5 minute sma( close ,  80 ) ) ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 12 | 14 | Disabled | root/group[cash\|any] | [0] 5 minute count( 100, 1 where daily abs( [0] 5 minute adx di positive( 250 ) - [0] 5 minute adx di negative( 250 ) ) > 0.4 ) = 0 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#8** `[0] 5 minute count( 320, 1 where [0] 5 minute dx_diff + 1.5 > 0 ) > 240` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[0] 5 minute count( 320, 1 where [0] 5 minute dx_diff + 1.5 < 3 ) crossed below 240` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#13** `[0] 5 minute sma( close ,  80 ) crossed below 0.05 * ( [0] 5 minute max( 1120 ,  [0] 5 minute sma( close ,  80 ) ) - [0] 5 minute min( 1120 ,  [0] 5 minute sma( close ,  80 ) ) )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **8** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `1 day ago close * 1 day ago volume > 100000000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `[0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) > 0`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `[0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) > [0] 5 minute max( 240 ,  [0] 5 minute dx_diff )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `[0] 5 minute dx_diff crossed above 0.9 * [0] 5 minute max( 650 ,  [0] 5 minute dx_diff )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `[0] 5 minute count( 650, 1 where [0] 5 minute dx_diff / [0] 5 minute max( 650 ,  [0] 5 minute dx_diff ) crossed above 0.6 ) crossed above 2`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `1 day ago close * 1 day ago volume > 100000000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `[0] 5 minute sma( close ,  156 ) crossed below 0.4`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `[0] 5 minute count( 100, 1 where daily abs( [0] 5 minute adx di positive( 250 ) - [0] 5 minute adx di negative( 250 ) ) > 0.4 ) = 0`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `custom_indicator_58577` — appears 9 time(s) in the expression tree
- `max` — appears 6 time(s) in the expression tree
- `abs` — appears 5 time(s) in the expression tree
- `adx di positive` — appears 5 time(s) in the expression tree
- `adx di negative` — appears 5 time(s) in the expression tree
- `count` — appears 4 time(s) in the expression tree
- `sma` — appears 4 time(s) in the expression tree
- `close` — appears 3 time(s) in the expression tree
- `volume` — appears 3 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 8 occurrence(s)
- `*` — 5 occurrence(s)
- `crossed above` — 3 occurrence(s)
- `crossed below` — 3 occurrence(s)
- `+` — 2 occurrence(s)
- `/` — 1 occurrence(s)
- `<` — 1 occurrence(s)
- `=` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **8** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Moving average, Momentum
- **Tags:** universe:cash, indicator:volume, indicator:sma, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

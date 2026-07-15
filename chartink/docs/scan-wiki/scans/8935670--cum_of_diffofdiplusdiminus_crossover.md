---
scan_id: 8935670
scan_name: CUM_OF_DIffofDIplusDIminus_Crossover
source_url: https://chartink.com/screener/test-2022-07-03-22
market: Indian equities
horizon: Intraday
classification: ["Oscillator", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "universe:cash", "indicator:adx", "indicator:volume", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 13
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Oscillator
---

# CUM_OF_DIffofDIplusDIminus_Crossover

## Source

- Chartink URL: https://chartink.com/screener/test-2022-07-03-22
- Scan ID: `8935670`
- Slug: `test-2022-07-03-22`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2022-07-03T16:09:48.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8935670.json](../source-snapshots/8935670.json)
- Text snapshot: [source-snapshots/8935670.txt](../source-snapshots/8935670.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **2** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Oscillator, Volume/delivery, Momentum, Multi-factor**.
The active tests, in captured order, are:
- 1 day ago close * 1 day ago volume > 100000000
- [0] 5 minute sum( close ,  200 ) crossed above 0

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: CUM_OF_DIffofDIplusDIminus_Crossover
Scan id: 8935670
Slug: test-2022-07-03-22
Source URL: https://chartink.com/screener/test-2022-07-03-22
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-07-03T16:09:48.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close * 1 day ago volume > 100000000
2. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Disabled] [0] 15 minute sum( close ,  300 ) crossed above 0
    group_path: root/group[cash|all]
4. [Disabled] [0] 60 minute sum( close ,  100 ) crossed above 0
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Disabled] [0] 5 minute sum( close ,  900 ) crossed below 0
    group_path: root/group[cash|all]
7. [Disabled] [0] 5 minute count( 100, 1 where [0] 5 minute adx di negative( 250 ) > [0] 5 minute adx di positive( 250 ) ) > 90
    group_path: root/group[cash|all]
8. [Disabled] [0] 60 minute sum( close ,  900 ) < -100
    group_path: root/group[cash|all]
9. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
10. [Disabled] [0] 5 minute sum( close ,  900 ) crossed above 0
    group_path: root/group[cash|all]
11. [Disabled] [0] 5 minute count( 100, 1 where [0] 5 minute adx di positive( 250 ) > [0] 5 minute adx di negative( 250 ) ) > 90
    group_path: root/group[cash|all]
12. [Disabled] [0] 60 minute sum( close ,  900 ) > 100
    group_path: root/group[cash|all]
13. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Disabled] [0] 5 minute sum( close ,  200 ) crossed below [-1] 5 minute min( 900 ,  [0] 5 minute sum( close ,  200 ) )
    group_path: root/group[cash|all]
15. [Disabled] [0] 5 minute sum( close ,  200 ) crossed above 0
    group_path: root/group[cash|all]
16. [Disabled] [-1] 5 minute count( 1000, 1 where [0] 5 minute sum( close ,  200 ) < 0 ) = 1000
    group_path: root/group[cash|all]
17. [Disabled] [0] 60 minute sum( close ,  900 ) > 100
    group_path: root/group[cash|all]
18. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
19. [Enabled] [0] 5 minute sum( close ,  200 ) crossed above 0
    group_path: root/group[cash|all]
20. [Disabled] [0] 5 minute sum( close ,  200 ) crossed below 0
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( 1 day ago close * 1 day ago volume > 100000000 and( cash ( [0] 5 minute sum( [0] 5 minute adx di positive( 250 ) - [0] 5 minute adx di negative( 250 ) , 200 ) > 0 and [ -1 ] 5 minute sum( [0] 5 minute adx di positive( 250 ) - [ -1 ] 5 minute adx di negative( 250 ) , 200 ) <= 0 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Disabled | root/group[cash\|all] | [0] 15 minute sum( close ,  300 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 4 | Disabled | root/group[cash\|all] | [0] 60 minute sum( close ,  100 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 6 | Disabled | root/group[cash\|all] | [0] 5 minute sum( close ,  900 ) crossed below 0 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 7 | Disabled | root/group[cash\|all] | [0] 5 minute count( 100, 1 where [0] 5 minute adx di negative( 250 ) > [0] 5 minute adx di positive( 250 ) ) > 90 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 8 | Disabled | root/group[cash\|all] | [0] 60 minute sum( close ,  900 ) < -100 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 10 | Disabled | root/group[cash\|all] | [0] 5 minute sum( close ,  900 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 11 | Disabled | root/group[cash\|all] | [0] 5 minute count( 100, 1 where [0] 5 minute adx di positive( 250 ) > [0] 5 minute adx di negative( 250 ) ) > 90 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 12 | Disabled | root/group[cash\|all] | [0] 60 minute sum( close ,  900 ) > 100 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 14 | Disabled | root/group[cash\|all] | [0] 5 minute sum( close ,  200 ) crossed below [-1] 5 minute min( 900 ,  [0] 5 minute sum( close ,  200 ) ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 15 | Disabled | root/group[cash\|all] | [0] 5 minute sum( close ,  200 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 16 | Disabled | root/group[cash\|all] | [-1] 5 minute count( 1000, 1 where [0] 5 minute sum( close ,  200 ) < 0 ) = 1000 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 17 | Disabled | root/group[cash\|all] | [0] 60 minute sum( close ,  900 ) > 100 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 19 | Enabled | root/group[cash\|all] | [0] 5 minute sum( close ,  200 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 20 | Disabled | root/group[cash\|all] | [0] 5 minute sum( close ,  200 ) crossed below 0 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#19** `[0] 5 minute sum( close ,  200 ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **13** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `[0] 15 minute sum( close ,  300 ) crossed above 0`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `[0] 60 minute sum( close ,  100 ) crossed above 0`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `[0] 5 minute sum( close ,  900 ) crossed below 0`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `[0] 5 minute count( 100, 1 where [0] 5 minute adx di negative( 250 ) > [0] 5 minute adx di positive( 250 ) ) > 90`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `[0] 60 minute sum( close ,  900 ) < -100`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `[0] 5 minute sum( close ,  900 ) crossed above 0`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `[0] 5 minute count( 100, 1 where [0] 5 minute adx di positive( 250 ) > [0] 5 minute adx di negative( 250 ) ) > 90`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `[0] 60 minute sum( close ,  900 ) > 100`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `[0] 5 minute sum( close ,  200 ) crossed below [-1] 5 minute min( 900 ,  [0] 5 minute sum( close ,  200 ) )`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #15
- **Condition (verbatim):** `[0] 5 minute sum( close ,  200 ) crossed above 0`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `[-1] 5 minute count( 1000, 1 where [0] 5 minute sum( close ,  200 ) < 0 ) = 1000`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #17
- **Condition (verbatim):** `[0] 60 minute sum( close ,  900 ) > 100`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #20
- **Condition (verbatim):** `[0] 5 minute sum( close ,  200 ) crossed below 0`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `adx di positive` — appears 15 time(s) in the expression tree
- `adx di negative` — appears 15 time(s) in the expression tree
- `sum` — appears 13 time(s) in the expression tree
- `count` — appears 3 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 7 occurrence(s)
- `crossed above` — 5 occurrence(s)
- `crossed below` — 3 occurrence(s)
- `<` — 2 occurrence(s)
- `*` — 1 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_days_ago`, `5_minute`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **13** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Oscillator, Volume/delivery, Momentum, Multi-factor
- **Tags:** bias:upward-condition, universe:cash, indicator:adx, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

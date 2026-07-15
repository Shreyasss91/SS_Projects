---
scan_id: 11585071
scan_name: three red bars
source_url: https://chartink.com/screener/three-red-bars-2
market: Indian equities
horizon: Swing
classification: ["Breakout"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 9
disabled_filter_count: 9
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Breakout
---

# three red bars

## Source

- Chartink URL: https://chartink.com/screener/three-red-bars-2
- Scan ID: `11585071`
- Slug: `three-red-bars-2`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-04-26T15:34:59.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11585071.json](../source-snapshots/11585071.json)
- Text snapshot: [source-snapshots/11585071.txt](../source-snapshots/11585071.txt)

## What this scan is for

This is a **swing** screen over **futures** with **9** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Breakout**.
The active tests, in captured order, are:
- 1 day ago count( 3, 1 where daily close < daily open ) = 3
- daily close > daily open
- daily high > 1 day ago max( 3 ,  daily open )
- daily close - daily open >= 1 day ago sum( close ,  3 )
- 1 day ago count( 3, 1 where daily close < daily open ) = 3
- daily count streak( 3, 1 where daily open - daily close < 1 day ago open - 1 day ago close ) = 3
- daily count( 3, 1 where daily close < daily open ) = 3
- daily count( 3, 1 where daily open > 1 day ago close ) = 3
- daily count streak( 3, 1 where daily open - daily close < 1 day ago open - 1 day ago close ) = 3

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: three red bars
Scan id: 11585071
Slug: three-red-bars-2
Source URL: https://chartink.com/screener/three-red-bars-2
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-26T15:34:59.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily count( 3, 1 where daily open = daily low ) >= 1
2. [Disabled] daily count( 3, 1 where daily close < daily open ) = 3
3. [Disabled] daily open - daily close < 1 day ago min( 2 ,  daily open - daily close )
4. [Disabled] daily count( 14, 1 where ( daily least - daily low ) / ( daily high - daily low ) > 0.4 ) crossed above 7
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] 1 day ago count( 3, 1 where daily close < daily open ) = 3
    group_path: root/group[cash|all]
7. [Enabled] daily close > daily open
    group_path: root/group[cash|all]
8. [Enabled] daily high > 1 day ago max( 3 ,  daily open )
    group_path: root/group[cash|all]
9. [Enabled] daily close - daily open >= 1 day ago sum( close ,  3 )
    group_path: root/group[cash|all]
10. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
11. [Enabled] 1 day ago count( 3, 1 where daily close < daily open ) = 3
    group_path: root/group[cash|all]
12. [Disabled] daily close > daily open
    group_path: root/group[cash|all]
13. [Disabled] daily high > 1 day ago max( 3 ,  daily open )
    group_path: root/group[cash|all]
14. [Enabled] daily count streak( 3, 1 where daily open - daily close < 1 day ago open - 1 day ago close ) = 3
    group_path: root/group[cash|all]
15. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
16. [Enabled] daily count( 3, 1 where daily close < daily open ) = 3
    group_path: root/group[cash|all]
17. [Disabled] daily close > daily open
    group_path: root/group[cash|all]
18. [Disabled] daily open > 1 day ago close
    group_path: root/group[cash|all]
19. [Disabled] daily high > 1 day ago high
    group_path: root/group[cash|all]
20. [Enabled] daily count( 3, 1 where daily open > 1 day ago close ) = 3
    group_path: root/group[cash|all]
21. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all])
22. [Enabled] daily count streak( 3, 1 where daily open - daily close < 1 day ago open - 1 day ago close ) = 3
    group_path: root/group[cash|all]/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( latest count( 3, 1 where latest close < latest open ) = 3 and latest count( 3, 1 where latest open > 1 day ago close ) = 3 and( cash ( latest countstreak( 3, 1 where latest open - latest close < 1 day ago open - 1 day ago close ) = 3 ) ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily count( 3, 1 where daily open = daily low ) >= 1 | Inequality test: left expression must be greater than or equal to right. Currently disabled in source — not applied when the scan runs. |
| 2 | 2 | Disabled | root | daily count( 3, 1 where daily close < daily open ) = 3 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 3 | 3 | Disabled | root | daily open - daily close < 1 day ago min( 2 ,  daily open - daily close ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. |
| 4 | 4 | Disabled | root | daily count( 14, 1 where ( daily least - daily low ) / ( daily high - daily low ) > 0.4 ) crossed above 7 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 5 | 6 | Enabled | root/group[cash\|all] | 1 day ago count( 3, 1 where daily close < daily open ) = 3 | Inequality test: left expression must be strictly less than right. |
| 6 | 7 | Enabled | root/group[cash\|all] | daily close > daily open | Inequality test: left expression must be strictly greater than right. |
| 7 | 8 | Enabled | root/group[cash\|all] | daily high > 1 day ago max( 3 ,  daily open ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. |
| 8 | 9 | Enabled | root/group[cash\|all] | daily close - daily open >= 1 day ago sum( close ,  3 ) | Inequality test: left expression must be greater than or equal to right. |
| 9 | 11 | Enabled | root/group[cash\|all] | 1 day ago count( 3, 1 where daily close < daily open ) = 3 | Inequality test: left expression must be strictly less than right. |
| 10 | 12 | Disabled | root/group[cash\|all] | daily close > daily open | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 11 | 13 | Disabled | root/group[cash\|all] | daily high > 1 day ago max( 3 ,  daily open ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 12 | 14 | Enabled | root/group[cash\|all] | daily count streak( 3, 1 where daily open - daily close < 1 day ago open - 1 day ago close ) = 3 | Inequality test: left expression must be strictly less than right. |
| 13 | 16 | Enabled | root/group[cash\|all] | daily count( 3, 1 where daily close < daily open ) = 3 | Inequality test: left expression must be strictly less than right. |
| 14 | 17 | Disabled | root/group[cash\|all] | daily close > daily open | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 15 | 18 | Disabled | root/group[cash\|all] | daily open > 1 day ago close | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 16 | 19 | Disabled | root/group[cash\|all] | daily high > 1 day ago high | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 17 | 20 | Enabled | root/group[cash\|all] | daily count( 3, 1 where daily open > 1 day ago close ) = 3 | Inequality test: left expression must be strictly greater than right. |
| 18 | 22 | Enabled | root/group[cash\|all]/group[cash\|all] | daily count streak( 3, 1 where daily open - daily close < 1 day ago open - 1 day ago close ) = 3 | Inequality test: left expression must be strictly less than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **9** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#6** `1 day ago count( 3, 1 where daily close < daily open ) = 3` — Inequality test: left expression must be strictly less than right.
- **#7** `daily close > daily open` — Inequality test: left expression must be strictly greater than right.
- **#8** `daily high > 1 day ago max( 3 ,  daily open )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars.
- **#9** `daily close - daily open >= 1 day ago sum( close ,  3 )` — Inequality test: left expression must be greater than or equal to right.
- **#11** `1 day ago count( 3, 1 where daily close < daily open ) = 3` — Inequality test: left expression must be strictly less than right.
- **#14** `daily count streak( 3, 1 where daily open - daily close < 1 day ago open - 1 day ago close ) = 3` — Inequality test: left expression must be strictly less than right.
- **#16** `daily count( 3, 1 where daily close < daily open ) = 3` — Inequality test: left expression must be strictly less than right.
- **#20** `daily count( 3, 1 where daily open > 1 day ago close ) = 3` — Inequality test: left expression must be strictly greater than right.
- **#22** `daily count streak( 3, 1 where daily open - daily close < 1 day ago open - 1 day ago close ) = 3` — Inequality test: left expression must be strictly less than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **9** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily count( 3, 1 where daily open = daily low ) >= 1`
- **Meaning:** Inequality test: left expression must be greater than or equal to right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `daily count( 3, 1 where daily close < daily open ) = 3`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `daily open - daily close < 1 day ago min( 2 ,  daily open - daily close )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `daily count( 14, 1 where ( daily least - daily low ) / ( daily high - daily low ) > 0.4 ) crossed above 7`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `daily close > daily open`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #13
- **Condition (verbatim):** `daily high > 1 day ago max( 3 ,  daily open )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #17
- **Condition (verbatim):** `daily close > daily open`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #18
- **Condition (verbatim):** `daily open > 1 day ago close`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #19
- **Condition (verbatim):** `daily high > 1 day ago high`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `open` — appears 21 time(s) in the expression tree
- `close` — appears 18 time(s) in the expression tree
- `count` — appears 7 time(s) in the expression tree
- `high` — appears 5 time(s) in the expression tree
- `low` — appears 3 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `count streak` — appears 2 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree
- `least` — appears 1 time(s) in the expression tree
- `sum` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 9 occurrence(s)
- `=` — 8 occurrence(s)
- `<` — 7 occurrence(s)
- `-` — 6 occurrence(s)
- `>=` — 2 occurrence(s)
- `crossed above` — 1 occurrence(s)
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
- Universe/segment: **futures**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **9** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Retains **9** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Breakout
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

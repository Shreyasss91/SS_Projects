---
scan_id: 2564238
scan_name: Copy - Bearish Patterns and Failures
source_url: https://chartink.com/screener/copy-bearish-patterns-and-failures-40
market: Indian equities
horizon: Swing
classification: ["Price action"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 25
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Price action
---

# Copy - Bearish Patterns and Failures

## Source

- Chartink URL: https://chartink.com/screener/copy-bearish-patterns-and-failures-40
- Scan ID: `2564238`
- Slug: `copy-bearish-patterns-and-failures-40`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-07-22T12:11:59.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2564238.json](../source-snapshots/2564238.json)
- Text snapshot: [source-snapshots/2564238.txt](../source-snapshots/2564238.txt)

## What this scan is for

This is a **swing** screen over **futures** with **25** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Price action**.
The active tests, in captured order, are:
- 2 days ago close > 2 days ago open
- ( 2 days ago open + 2 days ago close ) / 2 > 1 day ago close
- 1 day ago open > 1 day ago close
- 1 day ago open > 2 days ago close
- 1 day ago close > 2 days ago open
- ( 1 day ago open - 1 day ago close ) / ( 0.001 + ( 1 day ago high - 1 day ago low ) ) > 0.6
- 2 days ago open < 2 days ago close
- 1 day ago close < 1 day ago open
- 1 day ago close <= 2 days ago open
- 2 days ago close < 1 day ago open
- ( 1 day ago open - 1 day ago close ) > ( 2 days ago close - 2 days ago open )
- 2 days ago close > 2 days ago open
- 1 day ago open <= 2 days ago close
- 2 days ago open <= 1 day ago close
- 1 day ago high < 2 days ago high
- ( 1 day ago open - 1 day ago close ) < ( 2 days ago close - 2 days ago open )
- 3 days ago close > 3 days ago open
- ( ( 3 days ago close - 3 days ago open ) / ( 0.001 + 3 days ago high - 3 days ago low ) ) > 0.6
- 3 days ago open > 2 days ago close
- 2 days ago close > 2 days ago open
- ( 2 days ago high - 2 days ago low ) > ( 3 * ( 2 days ago close - 2 days ago open ) )
- 1 day ago open > 1 day ago close
- 1 day ago open < 2 days ago open
- daily high > 1 day ago high
- daily high > 2 days ago high

Author description (source metadata): Scanner to find Bearish Patterns and Failures

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - Bearish Patterns and Failures
Scan id: 2564238
Slug: copy-bearish-patterns-and-failures-40
Source URL: https://chartink.com/screener/copy-bearish-patterns-and-failures-40
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-22T12:11:59.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
2. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|any]/group[cash|all])
3. [Enabled] 2 days ago close > 2 days ago open
    group_path: root/group[cash|any]/group[cash|all]
4. [Enabled] ( 2 days ago open + 2 days ago close ) / 2 > 1 day ago close
    group_path: root/group[cash|any]/group[cash|all]
5. [Enabled] 1 day ago open > 1 day ago close
    group_path: root/group[cash|any]/group[cash|all]
6. [Enabled] 1 day ago open > 2 days ago close
    group_path: root/group[cash|any]/group[cash|all]
7. [Enabled] 1 day ago close > 2 days ago open
    group_path: root/group[cash|any]/group[cash|all]
8. [Enabled] ( 1 day ago open - 1 day ago close ) / ( 0.001 + ( 1 day ago high - 1 day ago low ) ) > 0.6
    group_path: root/group[cash|any]/group[cash|all]
9. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|any]/group[cash|all])
10. [Enabled] 2 days ago open < 2 days ago close
    group_path: root/group[cash|any]/group[cash|all]
11. [Enabled] 1 day ago close < 1 day ago open
    group_path: root/group[cash|any]/group[cash|all]
12. [Enabled] 1 day ago close <= 2 days ago open
    group_path: root/group[cash|any]/group[cash|all]
13. [Enabled] 2 days ago close < 1 day ago open
    group_path: root/group[cash|any]/group[cash|all]
14. [Enabled] ( 1 day ago open - 1 day ago close ) > ( 2 days ago close - 2 days ago open )
    group_path: root/group[cash|any]/group[cash|all]
15. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|any]/group[cash|all])
16. [Enabled] 2 days ago close > 2 days ago open
    group_path: root/group[cash|any]/group[cash|all]
17. [Enabled] 1 day ago open <= 2 days ago close
    group_path: root/group[cash|any]/group[cash|all]
18. [Enabled] 2 days ago open <= 1 day ago close
    group_path: root/group[cash|any]/group[cash|all]
19. [Enabled] 1 day ago high < 2 days ago high
    group_path: root/group[cash|any]/group[cash|all]
20. [Enabled] ( 1 day ago open - 1 day ago close ) < ( 2 days ago close - 2 days ago open )
    group_path: root/group[cash|any]/group[cash|all]
21. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|any]/group[cash|all])
22. [Enabled] 3 days ago close > 3 days ago open
    group_path: root/group[cash|any]/group[cash|all]
23. [Enabled] ( ( 3 days ago close - 3 days ago open ) / ( 0.001 + 3 days ago high - 3 days ago low ) ) > 0.6
    group_path: root/group[cash|any]/group[cash|all]
24. [Enabled] 3 days ago open > 2 days ago close
    group_path: root/group[cash|any]/group[cash|all]
25. [Enabled] 2 days ago close > 2 days ago open
    group_path: root/group[cash|any]/group[cash|all]
26. [Enabled] ( 2 days ago high - 2 days ago low ) > ( 3 * ( 2 days ago close - 2 days ago open ) )
    group_path: root/group[cash|any]/group[cash|all]
27. [Enabled] 1 day ago open > 1 day ago close
    group_path: root/group[cash|any]/group[cash|all]
28. [Enabled] 1 day ago open < 2 days ago open
    group_path: root/group[cash|any]/group[cash|all]
29. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
30. [Enabled] daily high > 1 day ago high
    group_path: root/group[cash|all]
31. [Enabled] daily high > 2 days ago high
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( ( cash ( 2 days ago close > 2 days ago open and( 2 days ago open + 2 days ago close ) / 2 > 1 day ago close and 1 day ago open > 1 day ago close and 1 day ago open > 2 days ago close and 1 day ago close > 2 days ago open and( 1 day ago open - 1 day ago close ) / ( 0.001 + ( 1 day ago high - 1 day ago low ) ) > 0.6 ) ) or( cash ( 2 days ago open < 2 days ago close and 1 day ago close < 1 day ago open and 1 day ago close <= 2 days ago open and 2 days ago close < 1 day ago open and( 1 day ago open - 1 day ago close ) > ( 2 days ago close - 2 days ago open ) ) ) or( cash ( 2 days ago close > 2 days ago open and 1 day ago open <= 2 days ago close and 2 days ago open <= 1 day ago close and 1 day ago high < 2 days ago high and( 1 day ago open - 1 day ago close ) < ( 2 days ago close - 2 days ago open ) ) ) or( cash ( 3 days ago close > 3 days ago open and( ( 3 days ago close - 3 days ago open ) / ( 0.001 + 3 days ago high - 3 days ago low ) ) > 0.6 and 3 days ago open > 2 days ago close and 2 days ago close > 2 days ago open and( 2 days ago high - 2 days ago low ) > ( 3 * ( 2 days ago close - 2 days ago open ) ) and 1 day ago open > 1 day ago close and 1 day ago open < 2 days ago open ) ) ) ) and( cash ( latest high > 1 day ago high and latest high > 2 days ago high ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 3 | Enabled | root/group[cash\|any]/group[cash\|all] | 2 days ago close > 2 days ago open | Inequality test: left expression must be strictly greater than right. |
| 2 | 4 | Enabled | root/group[cash\|any]/group[cash\|all] | ( 2 days ago open + 2 days ago close ) / 2 > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 3 | 5 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago open > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 4 | 6 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago open > 2 days ago close | Inequality test: left expression must be strictly greater than right. |
| 5 | 7 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago close > 2 days ago open | Inequality test: left expression must be strictly greater than right. |
| 6 | 8 | Enabled | root/group[cash\|any]/group[cash\|all] | ( 1 day ago open - 1 day ago close ) / ( 0.001 + ( 1 day ago high - 1 day ago low ) ) > 0.6 | Inequality test: left expression must be strictly greater than right. |
| 7 | 10 | Enabled | root/group[cash\|any]/group[cash\|all] | 2 days ago open < 2 days ago close | Inequality test: left expression must be strictly less than right. |
| 8 | 11 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago close < 1 day ago open | Inequality test: left expression must be strictly less than right. |
| 9 | 12 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago close <= 2 days ago open | Inequality test: left expression must be less than or equal to right. |
| 10 | 13 | Enabled | root/group[cash\|any]/group[cash\|all] | 2 days ago close < 1 day ago open | Inequality test: left expression must be strictly less than right. |
| 11 | 14 | Enabled | root/group[cash\|any]/group[cash\|all] | ( 1 day ago open - 1 day ago close ) > ( 2 days ago close - 2 days ago open ) | Inequality test: left expression must be strictly greater than right. |
| 12 | 16 | Enabled | root/group[cash\|any]/group[cash\|all] | 2 days ago close > 2 days ago open | Inequality test: left expression must be strictly greater than right. |
| 13 | 17 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago open <= 2 days ago close | Inequality test: left expression must be less than or equal to right. |
| 14 | 18 | Enabled | root/group[cash\|any]/group[cash\|all] | 2 days ago open <= 1 day ago close | Inequality test: left expression must be less than or equal to right. |
| 15 | 19 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago high < 2 days ago high | Inequality test: left expression must be strictly less than right. |
| 16 | 20 | Enabled | root/group[cash\|any]/group[cash\|all] | ( 1 day ago open - 1 day ago close ) < ( 2 days ago close - 2 days ago open ) | Inequality test: left expression must be strictly less than right. |
| 17 | 22 | Enabled | root/group[cash\|any]/group[cash\|all] | 3 days ago close > 3 days ago open | Inequality test: left expression must be strictly greater than right. |
| 18 | 23 | Enabled | root/group[cash\|any]/group[cash\|all] | ( ( 3 days ago close - 3 days ago open ) / ( 0.001 + 3 days ago high - 3 days ago low ) ) > 0.6 | Inequality test: left expression must be strictly greater than right. |
| 19 | 24 | Enabled | root/group[cash\|any]/group[cash\|all] | 3 days ago open > 2 days ago close | Inequality test: left expression must be strictly greater than right. |
| 20 | 25 | Enabled | root/group[cash\|any]/group[cash\|all] | 2 days ago close > 2 days ago open | Inequality test: left expression must be strictly greater than right. |
| 21 | 26 | Enabled | root/group[cash\|any]/group[cash\|all] | ( 2 days ago high - 2 days ago low ) > ( 3 * ( 2 days ago close - 2 days ago open ) ) | Inequality test: left expression must be strictly greater than right. |
| 22 | 27 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago open > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 23 | 28 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 day ago open < 2 days ago open | Inequality test: left expression must be strictly less than right. |
| 24 | 30 | Enabled | root/group[cash\|all] | daily high > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 25 | 31 | Enabled | root/group[cash\|all] | daily high > 2 days ago high | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **25** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `2 days ago close > 2 days ago open` — Inequality test: left expression must be strictly greater than right.
- **#4** `( 2 days ago open + 2 days ago close ) / 2 > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#5** `1 day ago open > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#6** `1 day ago open > 2 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#7** `1 day ago close > 2 days ago open` — Inequality test: left expression must be strictly greater than right.
- **#8** `( 1 day ago open - 1 day ago close ) / ( 0.001 + ( 1 day ago high - 1 day ago low ) ) > 0.6` — Inequality test: left expression must be strictly greater than right.
- **#10** `2 days ago open < 2 days ago close` — Inequality test: left expression must be strictly less than right.
- **#11** `1 day ago close < 1 day ago open` — Inequality test: left expression must be strictly less than right.
- **#12** `1 day ago close <= 2 days ago open` — Inequality test: left expression must be less than or equal to right.
- **#13** `2 days ago close < 1 day ago open` — Inequality test: left expression must be strictly less than right.
- **#14** `( 1 day ago open - 1 day ago close ) > ( 2 days ago close - 2 days ago open )` — Inequality test: left expression must be strictly greater than right.
- **#16** `2 days ago close > 2 days ago open` — Inequality test: left expression must be strictly greater than right.
- **#17** `1 day ago open <= 2 days ago close` — Inequality test: left expression must be less than or equal to right.
- **#18** `2 days ago open <= 1 day ago close` — Inequality test: left expression must be less than or equal to right.
- **#19** `1 day ago high < 2 days ago high` — Inequality test: left expression must be strictly less than right.
- **#20** `( 1 day ago open - 1 day ago close ) < ( 2 days ago close - 2 days ago open )` — Inequality test: left expression must be strictly less than right.
- **#22** `3 days ago close > 3 days ago open` — Inequality test: left expression must be strictly greater than right.
- **#23** `( ( 3 days ago close - 3 days ago open ) / ( 0.001 + 3 days ago high - 3 days ago low ) ) > 0.6` — Inequality test: left expression must be strictly greater than right.
- **#24** `3 days ago open > 2 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#25** `2 days ago close > 2 days ago open` — Inequality test: left expression must be strictly greater than right.
- **#26** `( 2 days ago high - 2 days ago low ) > ( 3 * ( 2 days ago close - 2 days ago open ) )` — Inequality test: left expression must be strictly greater than right.
- **#27** `1 day ago open > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#28** `1 day ago open < 2 days ago open` — Inequality test: left expression must be strictly less than right.
- **#30** `daily high > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#31** `daily high > 2 days ago high` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `open` — appears 25 time(s) in the expression tree
- `close` — appears 24 time(s) in the expression tree
- `high` — appears 9 time(s) in the expression tree
- `low` — appears 3 time(s) in the expression tree

### Operators observed
- `>` — 16 occurrence(s)
- `<` — 6 occurrence(s)
- `<=` — 3 occurrence(s)
- `/` — 2 occurrence(s)
- `-` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **25** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Price action
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

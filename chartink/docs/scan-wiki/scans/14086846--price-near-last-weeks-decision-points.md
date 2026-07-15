---
scan_id: 14086846
scan_name: "price near last week's decision points"
source_url: https://chartink.com/screener/price-near-last-week-s-decision-points
market: Indian equities
horizon: Multi-horizon
classification: ["Price action"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "timeframe:daily", "timeframe:monthly", "timeframe:weekly", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 9
disabled_filter_count: 5
needs_review_filter_count: 0
root_segment: futures
root_join: any
primary_classification: Price action
---

# price near last week's decision points

## Source

- Chartink URL: https://chartink.com/screener/price-near-last-week-s-decision-points
- Scan ID: `14086846`
- Slug: `price-near-last-week-s-decision-points`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2023-12-06T14:02:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14086846.json](../source-snapshots/14086846.json)
- Text snapshot: [source-snapshots/14086846.txt](../source-snapshots/14086846.txt)

## What this scan is for

This is a **multi-horizon** screen over **futures** with **9** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Price action**.
The active tests, in captured order, are:
- [-1] 5 minute low > 1 week ago close
- [-2] 5 minute count( 4, 1 where [0] 5 minute low > 1 week ago close ) = 4
- [0] 5 minute low < 1 week ago close
- [-1] 5 minute low > 1 month ago close
- [0] 5 minute low < 1 month ago close
- [-1] 5 minute low > 1 week ago low * 1.0025
- [0] 5 minute low < 1 week ago low * 1.0025
- [0] 5 minute low < 1 week ago high * 1.0025
- [-1] 5 minute low > 1 week ago high * 1.0025

Author description (source metadata): Decision points could be previous week's close, low, high etc,.

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: price near last week's decision points
Scan id: 14086846
Slug: price-near-last-week-s-decision-points
Source URL: https://chartink.com/screener/price-near-last-week-s-decision-points
Root universe/segment: futures
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-06T14:02:56.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Disabled] daily open > 1 day ago close * 1.01
    group_path: root/group[cash|all]
3. [Enabled] [-1] 5 minute low > 1 week ago close
    group_path: root/group[cash|all]
4. [Enabled] [-2] 5 minute count( 4, 1 where [0] 5 minute low > 1 week ago close ) = 4
    group_path: root/group[cash|all]
5. [Enabled] [0] 5 minute low < 1 week ago close
    group_path: root/group[cash|all]
6. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Disabled] daily open > 1 day ago close * 1.01
    group_path: root/group[cash|all]
8. [Enabled] [-1] 5 minute low > 1 month ago close
    group_path: root/group[cash|all]
9. [Disabled] [-2] 5 minute count( 4, 1 where [0] 5 minute low > 1 month ago close ) = 4
    group_path: root/group[cash|all]
10. [Enabled] [0] 5 minute low < 1 month ago close
    group_path: root/group[cash|all]
11. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
12. [Disabled] daily open > 1 day ago close * 1.01
    group_path: root/group[cash|all]
13. [Enabled] [-1] 5 minute low > 1 week ago low * 1.0025
    group_path: root/group[cash|all]
14. [Enabled] [0] 5 minute low < 1 week ago low * 1.0025
    group_path: root/group[cash|all]
15. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
16. [Disabled] daily open > 1 day ago close * 1.01
    group_path: root/group[cash|all]
17. [Enabled] [0] 5 minute low < 1 week ago high * 1.0025
    group_path: root/group[cash|all]
18. [Enabled] [-1] 5 minute low > 1 week ago high * 1.0025
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( [-1] 5 minute low > 1 month ago close and [0] 5 minute low < 1 month ago close ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Disabled | root/group[cash\|all] | daily open > 1 day ago close * 1.01 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 2 | 3 | Enabled | root/group[cash\|all] | [-1] 5 minute low > 1 week ago close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset. |
| 3 | 4 | Enabled | root/group[cash\|all] | [-2] 5 minute count( 4, 1 where [0] 5 minute low > 1 week ago close ) = 4 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset. |
| 4 | 5 | Enabled | root/group[cash\|all] | [0] 5 minute low < 1 week ago close | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset. |
| 5 | 7 | Disabled | root/group[cash\|all] | daily open > 1 day ago close * 1.01 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 6 | 8 | Enabled | root/group[cash\|all] | [-1] 5 minute low > 1 month ago close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References monthly bars / monthly offset. |
| 7 | 9 | Disabled | root/group[cash\|all] | [-2] 5 minute count( 4, 1 where [0] 5 minute low > 1 month ago close ) = 4 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. References monthly bars / monthly offset. |
| 8 | 10 | Enabled | root/group[cash\|all] | [0] 5 minute low < 1 month ago close | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References monthly bars / monthly offset. |
| 9 | 12 | Disabled | root/group[cash\|all] | daily open > 1 day ago close * 1.01 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 10 | 13 | Enabled | root/group[cash\|all] | [-1] 5 minute low > 1 week ago low * 1.0025 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset. |
| 11 | 14 | Enabled | root/group[cash\|all] | [0] 5 minute low < 1 week ago low * 1.0025 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset. |
| 12 | 16 | Disabled | root/group[cash\|all] | daily open > 1 day ago close * 1.01 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 13 | 17 | Enabled | root/group[cash\|all] | [0] 5 minute low < 1 week ago high * 1.0025 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset. |
| 14 | 18 | Enabled | root/group[cash\|all] | [-1] 5 minute low > 1 week ago high * 1.0025 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **9** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `[-1] 5 minute low > 1 week ago close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset.
- **#4** `[-2] 5 minute count( 4, 1 where [0] 5 minute low > 1 week ago close ) = 4` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset.
- **#5** `[0] 5 minute low < 1 week ago close` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset.
- **#8** `[-1] 5 minute low > 1 month ago close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References monthly bars / monthly offset.
- **#10** `[0] 5 minute low < 1 month ago close` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References monthly bars / monthly offset.
- **#13** `[-1] 5 minute low > 1 week ago low * 1.0025` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset.
- **#14** `[0] 5 minute low < 1 week ago low * 1.0025` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset.
- **#17** `[0] 5 minute low < 1 week ago high * 1.0025` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset.
- **#18** `[-1] 5 minute low > 1 week ago high * 1.0025` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. References weekly bars / weekly offset.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **5** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #2
- **Condition (verbatim):** `daily open > 1 day ago close * 1.01`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `daily open > 1 day ago close * 1.01`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `[-2] 5 minute count( 4, 1 where [0] 5 minute low > 1 month ago close ) = 4`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `daily open > 1 day ago close * 1.01`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `daily open > 1 day ago close * 1.01`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `low` — appears 12 time(s) in the expression tree
- `close` — appears 10 time(s) in the expression tree
- `open` — appears 4 time(s) in the expression tree
- `count` — appears 2 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 10 occurrence(s)
- `*` — 8 occurrence(s)
- `<` — 4 occurrence(s)
- `=` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `1_months_ago`, `1_weeks_ago`, `5_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **9** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **5** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Price action
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, timeframe:daily, timeframe:monthly, timeframe:weekly, timeframe:intraday-bars
- **Root universe:** futures
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

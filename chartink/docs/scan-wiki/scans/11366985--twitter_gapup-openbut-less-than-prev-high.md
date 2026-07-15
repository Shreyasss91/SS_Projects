---
scan_id: 11366985
scan_name: twitter_Gapup openbut less than prev high
source_url: https://chartink.com/screener/test-2023-03-28-6
market: Indian equities
horizon: Swing
classification: ["Price action"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: any
primary_classification: Price action
---

# twitter_Gapup openbut less than prev high

## Source

- Chartink URL: https://chartink.com/screener/test-2023-03-28-6
- Scan ID: `11366985`
- Slug: `test-2023-03-28-6`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-03-28T07:22:03.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11366985.json](../source-snapshots/11366985.json)
- Text snapshot: [source-snapshots/11366985.txt](../source-snapshots/11366985.txt)

## What this scan is for

This is a **swing** screen over **futures** with **4** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Price action**.
The active tests, in captured order, are:
- daily open < 1 day ago high
- daily open > 1 day ago close * 1.01
- daily open > 1 day ago low
- daily open < 1 day ago close * 0.99

Author description (source metadata): https://twitter.com/Suresh_kumar047/status/1640563092898676736?t=RIkmZit9Mki1fqaSIG43dw&s=19

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: twitter_Gapup openbut less than prev high
Scan id: 11366985
Slug: test-2023-03-28-6
Source URL: https://chartink.com/screener/test-2023-03-28-6
Root universe/segment: futures
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-03-28T07:22:03.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily open < 1 day ago high
    group_path: root/group[cash|all]
3. [Enabled] daily open > 1 day ago close * 1.01
    group_path: root/group[cash|all]
4. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] daily open > 1 day ago low
    group_path: root/group[cash|all]
6. [Enabled] daily open < 1 day ago close * 0.99
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( latest open < 1 day ago high and latest open > 1 day ago close * 1.01 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily open < 1 day ago high | Inequality test: left expression must be strictly less than right. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily open > 1 day ago close * 1.01 | Inequality test: left expression must be strictly greater than right. |
| 3 | 5 | Enabled | root/group[cash\|all] | daily open > 1 day ago low | Inequality test: left expression must be strictly greater than right. |
| 4 | 6 | Enabled | root/group[cash\|all] | daily open < 1 day ago close * 0.99 | Inequality test: left expression must be strictly less than right. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily open < 1 day ago high` — Inequality test: left expression must be strictly less than right.
- **#3** `daily open > 1 day ago close * 1.01` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily open > 1 day ago low` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily open < 1 day ago close * 0.99` — Inequality test: left expression must be strictly less than right.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `open` — appears 4 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 2 occurrence(s)
- `>` — 2 occurrence(s)
- `*` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`

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

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Price action
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, timeframe:daily
- **Root universe:** futures
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

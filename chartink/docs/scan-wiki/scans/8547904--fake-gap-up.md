---
scan_id: 8547904
scan_name: fake gap up
source_url: https://chartink.com/screener/fake-gap-up-1
market: Indian equities
horizon: Swing
classification: ["Price action"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-200", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Price action
---

# fake gap up

## Source

- Chartink URL: https://chartink.com/screener/fake-gap-up-1
- Scan ID: `8547904`
- Slug: `fake-gap-up-1`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2022-05-10T07:28:17.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8547904.json](../source-snapshots/8547904.json)
- Text snapshot: [source-snapshots/8547904.txt](../source-snapshots/8547904.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **4** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Price action**.
The active tests, in captured order, are:
- 1 day ago low / 4 days ago low > 0.99
- 1 day ago low / 4 days ago low < 1.01
- daily open > 1 day ago close * 1.01
- 1 day ago close < 1 day ago open

Author description (source metadata): see it in morning.

Backtest results you see is the output of screener on that days' morning

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: fake gap up
Scan id: 8547904
Slug: fake-gap-up-1
Source URL: https://chartink.com/screener/fake-gap-up-1
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-05-10T07:28:17.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago low / 4 days ago low > 0.99
    group_path: root/group[cash|all]
3. [Enabled] 1 day ago low / 4 days ago low < 1.01
    group_path: root/group[cash|all]
4. [Disabled] daily open > 4 days ago low * 1.035
    group_path: root/group[cash|all]
5. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] daily open > 1 day ago close * 1.01
    group_path: root/group[cash|all]
7. [Enabled] 1 day ago close < 1 day ago open
    group_path: root/group[cash|all]
8. [Disabled] daily open < 1 day ago open
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( 1 day ago low / 4 days ago low > 0.99 and 1 day ago low / 4 days ago low < 1.01 ) ) and( cash ( latest open > 1 day ago close * 1.01 and 1 day ago close < 1 day ago open ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago low / 4 days ago low > 0.99 | Inequality test: left expression must be strictly greater than right. |
| 2 | 3 | Enabled | root/group[cash\|all] | 1 day ago low / 4 days ago low < 1.01 | Inequality test: left expression must be strictly less than right. |
| 3 | 4 | Disabled | root/group[cash\|all] | daily open > 4 days ago low * 1.035 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 4 | 6 | Enabled | root/group[cash\|all] | daily open > 1 day ago close * 1.01 | Inequality test: left expression must be strictly greater than right. |
| 5 | 7 | Enabled | root/group[cash\|all] | 1 day ago close < 1 day ago open | Inequality test: left expression must be strictly less than right. |
| 6 | 8 | Disabled | root/group[cash\|all] | daily open < 1 day ago open | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago low / 4 days ago low > 0.99` — Inequality test: left expression must be strictly greater than right.
- **#3** `1 day ago low / 4 days ago low < 1.01` — Inequality test: left expression must be strictly less than right.
- **#6** `daily open > 1 day ago close * 1.01` — Inequality test: left expression must be strictly greater than right.
- **#7** `1 day ago close < 1 day ago open` — Inequality test: left expression must be strictly less than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #4
- **Condition (verbatim):** `daily open > 4 days ago low * 1.035`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `daily open < 1 day ago open`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `low` — appears 5 time(s) in the expression tree
- `open` — appears 5 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 3 occurrence(s)
- `<` — 3 occurrence(s)
- `/` — 2 occurrence(s)
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
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `3_days_ago`, `4_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Price action
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-200, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

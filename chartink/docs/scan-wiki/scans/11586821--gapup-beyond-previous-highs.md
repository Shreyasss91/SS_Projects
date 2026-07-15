---
scan_id: 11586821
scan_name: gapup beyond previous highs
source_url: https://chartink.com/screener/gapup-beyond-yesterday-s-high
market: Indian equities
horizon: "Swing"
classification: ["Other"]
tags: ["universe:futures","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Other
---

# gapup beyond previous highs

## Source

- Chartink URL: https://chartink.com/screener/gapup-beyond-yesterday-s-high
- Scan ID: `11586821`
- Slug: `gapup-beyond-yesterday-s-high`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-04-26T18:32:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11586821.json](../source-snapshots/11586821.json)
- Text snapshot: [source-snapshots/11586821.txt](../source-snapshots/11586821.txt)

## What this scan is for

This is a **swing** screen over **futures** with **3** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Other**.

The active tests, in captured order:
- daily open > 1 day ago max( 6 ,  daily high )
- daily open > 1 day ago max( 6 ,  daily open )
- daily open > 1 day ago max( 6 ,  daily close )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: gapup beyond previous highs
Scan id: 11586821
Slug: gapup-beyond-yesterday-s-high
Source URL: https://chartink.com/screener/gapup-beyond-yesterday-s-high
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-26T18:32:56.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily open > 1 day ago max( 6 ,  daily high )
    group_path: root/group[cash|all]
3. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
4. [Enabled] daily open > 1 day ago max( 6 ,  daily open )
    group_path: root/group[cash|all]
5. [Enabled] daily open > 1 day ago max( 6 ,  daily close )
    group_path: root/group[cash|all]
6. [Disabled] daily open > 1 day ago high
7. [Disabled] 1 day ago close < 2 days ago close

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( latest open > 1 day ago max( 6 , latest high ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily open > 1 day ago max( 6 ,  daily high ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. |
| 2 | 4 | Enabled | root/group[cash\|all] | daily open > 1 day ago max( 6 ,  daily open ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. |
| 3 | 5 | Enabled | root/group[cash\|all] | daily open > 1 day ago max( 6 ,  daily close ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. |
| 4 | 6 | Disabled | root | daily open > 1 day ago high | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 5 | 7 | Disabled | root | 1 day ago close < 2 days ago close | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily open > 1 day ago max( 6 ,  daily high )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars.
- **#4** `daily open > 1 day ago max( 6 ,  daily open )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars.
- **#5** `daily open > 1 day ago max( 6 ,  daily close )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #6
- **Condition (verbatim):** `daily open > 1 day ago high`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `1 day ago close < 2 days ago close`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `open` — appears 5 time(s) in the expression tree
- `max` — appears 3 time(s) in the expression tree
- `close` — appears 3 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 4 occurrence(s)
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
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`

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

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Other
- **Tags:** universe:futures, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

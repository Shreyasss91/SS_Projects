---
scan_id: 1464776
scan_name: "Copy - Gap Up by 3% with 3x volume."
source_url: https://chartink.com/screener/copy-gap-up-by-3-with-3x-volume-1520
market: Indian equities
horizon: Swing
classification: ["Volume/delivery"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "indicator:volume", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 7
disabled_filter_count: 4
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# Copy - Gap Up by 3% with 3x volume.

## Source

- Chartink URL: https://chartink.com/screener/copy-gap-up-by-3-with-3x-volume-1520
- Scan ID: `1464776`
- Slug: `copy-gap-up-by-3-with-3x-volume-1520`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2019-11-29T14:17:10.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1464776.json](../source-snapshots/1464776.json)
- Text snapshot: [source-snapshots/1464776.txt](../source-snapshots/1464776.txt)

## What this scan is for

This is a **swing** screen over **futures** with **7** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Volume/delivery**.
The active tests, in captured order, are:
- 1 day ago close * 1 day ago volume > 100000000
- daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
- daily count streak( 3, 1 where 1 day ago open > 2 days ago close ) = 3
- daily count streak( 3, 1 where 1 day ago close > 1 day ago open ) = 3
- daily open < 1 day ago close * 1
- daily close < daily open * 1
- daily close > 2 days ago close * 1

Author description (source metadata): Gap Up by 3% with 3x volume

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - Gap Up by 3% with 3x volume.
Scan id: 1464776
Slug: copy-gap-up-by-3-with-3x-volume-1520
Source URL: https://chartink.com/screener/copy-gap-up-by-3-with-3x-volume-1520
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-29T14:17:10.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
    group_path: root/group[cash|all]
4. [Disabled] daily volume > 1 day ago sma( close ,  7 ) * 2
5. [Disabled] daily open > 1 day ago close * 1.02
6. [Disabled] daily close < 1 day ago close * 0.98
7. [Enabled] daily count streak( 3, 1 where 1 day ago open > 2 days ago close ) = 3
8. [Disabled] daily count streak( 3, 1 where 1 day ago close > 2 days ago close ) = 3
9. [Enabled] daily count streak( 3, 1 where 1 day ago close > 1 day ago open ) = 3
10. [Enabled] daily open < 1 day ago close * 1
11. [Enabled] daily close < daily open * 1
12. [Enabled] daily close > 2 days ago close * 1

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and latest count( 200, 1 where( latest high / latest low ) = 1 ) < 1 ) ) and latest countstreak( 3, 1 where 1 day ago open > 2 days ago close ) = 3 and latest countstreak( 3, 1 where 1 day ago close > 1 day ago open ) = 3 and latest open < 1 day ago close * 1 and latest close < latest open * 1 and latest close > 2 days ago close * 1 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1 | Inequality test: left expression must be strictly less than right. |
| 3 | 4 | Disabled | root | daily volume > 1 day ago sma( close ,  7 ) * 2 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 4 | 5 | Disabled | root | daily open > 1 day ago close * 1.02 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 5 | 6 | Disabled | root | daily close < 1 day ago close * 0.98 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 6 | 7 | Enabled | root | daily count streak( 3, 1 where 1 day ago open > 2 days ago close ) = 3 | Inequality test: left expression must be strictly greater than right. |
| 7 | 8 | Disabled | root | daily count streak( 3, 1 where 1 day ago close > 2 days ago close ) = 3 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 8 | 9 | Enabled | root | daily count streak( 3, 1 where 1 day ago close > 1 day ago open ) = 3 | Inequality test: left expression must be strictly greater than right. |
| 9 | 10 | Enabled | root | daily open < 1 day ago close * 1 | Inequality test: left expression must be strictly less than right. |
| 10 | 11 | Enabled | root | daily close < daily open * 1 | Inequality test: left expression must be strictly less than right. |
| 11 | 12 | Enabled | root | daily close > 2 days ago close * 1 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **7** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1` — Inequality test: left expression must be strictly less than right.
- **#7** `daily count streak( 3, 1 where 1 day ago open > 2 days ago close ) = 3` — Inequality test: left expression must be strictly greater than right.
- **#9** `daily count streak( 3, 1 where 1 day ago close > 1 day ago open ) = 3` — Inequality test: left expression must be strictly greater than right.
- **#10** `daily open < 1 day ago close * 1` — Inequality test: left expression must be strictly less than right.
- **#11** `daily close < daily open * 1` — Inequality test: left expression must be strictly less than right.
- **#12** `daily close > 2 days ago close * 1` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **4** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #4
- **Condition (verbatim):** `daily volume > 1 day ago sma( close ,  7 ) * 2`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily open > 1 day ago close * 1.02`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `daily close < 1 day ago close * 0.98`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `daily count streak( 3, 1 where 1 day ago close > 2 days ago close ) = 3`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 12 time(s) in the expression tree
- `open` — appears 5 time(s) in the expression tree
- `volume` — appears 3 time(s) in the expression tree
- `count streak` — appears 3 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree

### Operators observed
- `*` — 7 occurrence(s)
- `>` — 7 occurrence(s)
- `<` — 4 occurrence(s)
- `=` — 4 occurrence(s)

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
- **Method context:** Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **7** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **4** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, indicator:volume, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

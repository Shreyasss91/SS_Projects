---
scan_id: 4777713
scan_name: Copy - Bullish Tasuki Line
source_url: https://chartink.com/screener/copy-bullish-tasuki-line-38
market: Indian equities
horizon: Swing
classification: ["Volume/delivery", "Breakout"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "indicator:volume", "timeframe:daily", "timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 14
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# Copy - Bullish Tasuki Line

## Source

- Chartink URL: https://chartink.com/screener/copy-bullish-tasuki-line-38
- Scan ID: `4777713`
- Slug: `copy-bullish-tasuki-line-38`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2021-06-02T14:25:32.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4777713.json](../source-snapshots/4777713.json)
- Text snapshot: [source-snapshots/4777713.txt](../source-snapshots/4777713.txt)

## What this scan is for

This is a **swing** screen over **futures** with **14** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Volume/delivery, Breakout**.
The active tests, in captured order, are:
- 1 day ago open > 1 day ago close
- daily open > 1 day ago close
- daily low > 1 day ago low
- daily close > 1 day ago high
- daily open < 1 day ago open
- daily volume > 1 day ago volume
- 21 days ago open > 21 days ago close
- 20 days ago open > 21 days ago close
- 20 days ago low > 21 days ago low
- 20 days ago close > 21 days ago high
- 20 days ago open < 21 days ago open
- 20 days ago volume > 21 days ago volume
- daily close < 20 days ago close * 0.9
- daily close < daily max( 14 ,  daily high ) * 0.95

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - Bullish Tasuki Line
Scan id: 4777713
Slug: copy-bullish-tasuki-line-38
Source URL: https://chartink.com/screener/copy-bullish-tasuki-line-38
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-02T14:25:32.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago open > 1 day ago close
    group_path: root/group[cash|all]
3. [Enabled] daily open > 1 day ago close
    group_path: root/group[cash|all]
4. [Enabled] daily low > 1 day ago low
    group_path: root/group[cash|all]
5. [Enabled] daily close > 1 day ago high
    group_path: root/group[cash|all]
6. [Enabled] daily open < 1 day ago open
    group_path: root/group[cash|all]
7. [Enabled] daily volume > 1 day ago volume
    group_path: root/group[cash|all]
8. [Disabled] daily volume > daily max( 50 ,  1 day ago volume )
    group_path: root/group[cash|all]
9. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
10. [Enabled] 21 days ago open > 21 days ago close
    group_path: root/group[cash|all]
11. [Enabled] 20 days ago open > 21 days ago close
    group_path: root/group[cash|all]
12. [Enabled] 20 days ago low > 21 days ago low
    group_path: root/group[cash|all]
13. [Enabled] 20 days ago close > 21 days ago high
    group_path: root/group[cash|all]
14. [Enabled] 20 days ago open < 21 days ago open
    group_path: root/group[cash|all]
15. [Enabled] 20 days ago volume > 21 days ago volume
    group_path: root/group[cash|all]
16. [Disabled] 20 days ago volume > daily max( 50 ,  1 day ago volume )
    group_path: root/group[cash|all]
17. [Enabled] daily close < 20 days ago close * 0.9
    group_path: root/group[cash|all]
18. [Enabled] daily close < daily max( 14 ,  daily high ) * 0.95
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( 21 days ago open > 21 days ago close and 20 days ago open > 21 days ago close and 20 days ago low > 21 days ago low and 20 days ago close > 21 days ago high and 20 days ago open < 21 days ago open and 20 days ago volume > 21 days ago volume and latest close < 20 days ago close * 0.9 and latest close < latest max( 14 , latest high ) * 0.95 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago open > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily open > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily low > 1 day ago low | Inequality test: left expression must be strictly greater than right. |
| 4 | 5 | Enabled | root/group[cash\|all] | daily close > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 5 | 6 | Enabled | root/group[cash\|all] | daily open < 1 day ago open | Inequality test: left expression must be strictly less than right. |
| 6 | 7 | Enabled | root/group[cash\|all] | daily volume > 1 day ago volume | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 7 | 8 | Disabled | root/group[cash\|all] | daily volume > daily max( 50 ,  1 day ago volume ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. |
| 8 | 10 | Enabled | root/group[cash\|all] | 21 days ago open > 21 days ago close | Inequality test: left expression must be strictly greater than right. |
| 9 | 11 | Enabled | root/group[cash\|all] | 20 days ago open > 21 days ago close | Inequality test: left expression must be strictly greater than right. |
| 10 | 12 | Enabled | root/group[cash\|all] | 20 days ago low > 21 days ago low | Inequality test: left expression must be strictly greater than right. |
| 11 | 13 | Enabled | root/group[cash\|all] | 20 days ago close > 21 days ago high | Inequality test: left expression must be strictly greater than right. |
| 12 | 14 | Enabled | root/group[cash\|all] | 20 days ago open < 21 days ago open | Inequality test: left expression must be strictly less than right. |
| 13 | 15 | Enabled | root/group[cash\|all] | 20 days ago volume > 21 days ago volume | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 14 | 16 | Disabled | root/group[cash\|all] | 20 days ago volume > daily max( 50 ,  1 day ago volume ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. |
| 15 | 17 | Enabled | root/group[cash\|all] | daily close < 20 days ago close * 0.9 | Inequality test: left expression must be strictly less than right. |
| 16 | 18 | Enabled | root/group[cash\|all] | daily close < daily max( 14 ,  daily high ) * 0.95 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **14** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago open > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#3** `daily open > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#4** `daily low > 1 day ago low` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily close > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily open < 1 day ago open` — Inequality test: left expression must be strictly less than right.
- **#7** `daily volume > 1 day ago volume` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#10** `21 days ago open > 21 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#11** `20 days ago open > 21 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#12** `20 days ago low > 21 days ago low` — Inequality test: left expression must be strictly greater than right.
- **#13** `20 days ago close > 21 days ago high` — Inequality test: left expression must be strictly greater than right.
- **#14** `20 days ago open < 21 days ago open` — Inequality test: left expression must be strictly less than right.
- **#15** `20 days ago volume > 21 days ago volume` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#17** `daily close < 20 days ago close * 0.9` — Inequality test: left expression must be strictly less than right.
- **#18** `daily close < daily max( 14 ,  daily high ) * 0.95` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #8
- **Condition (verbatim):** `daily volume > daily max( 50 ,  1 day ago volume )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `20 days ago volume > daily max( 50 ,  1 day ago volume )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 9 time(s) in the expression tree
- `open` — appears 8 time(s) in the expression tree
- `volume` — appears 8 time(s) in the expression tree
- `low` — appears 4 time(s) in the expression tree
- `high` — appears 3 time(s) in the expression tree
- `max` — appears 3 time(s) in the expression tree

### Operators observed
- `>` — 12 occurrence(s)
- `<` — 4 occurrence(s)
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
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `1_days_ago`, `20_days_ago`, `21_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Breakout.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **14** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery, Breakout
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, indicator:volume, timeframe:daily, timeframe:weekly
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

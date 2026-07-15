---
scan_id: 25084558
scan_name: Weakness DTF
source_url: https://chartink.com/screener/weakness-dtf
market: Indian equities
horizon: "Swing"
classification: ["Volatility","Momentum"]
tags: ["universe:nifty-200","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 9
disabled_filter_count: 5
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Volatility
---

# Weakness DTF

## Source

- Chartink URL: https://chartink.com/screener/weakness-dtf
- Scan ID: `25084558`
- Slug: `weakness-dtf`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2026-01-15T13:16:04.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/25084558.json](../source-snapshots/25084558.json)
- Text snapshot: [source-snapshots/25084558.txt](../source-snapshots/25084558.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **9** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volatility, Momentum**.

The active tests, in captured order:
- daily close < 1 day ago low + ( 0.1 * daily avg true range( 14 ) )
- daily high / daily open < 1.01
- daily avg true range( 1 ) > daily avg true range( 14 )
- ( daily close - daily low ) / ( daily high - daily low ) > 0.4
- ( daily close - daily low ) / ( daily high - daily low ) < 0.7
- daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) )
- ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 crossed below -0.01
- ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 > -0.015
- ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 crossed above 0.02

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Weakness DTF
Scan id: 25084558
Slug: weakness-dtf
Source URL: https://chartink.com/screener/weakness-dtf
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2026-01-15T13:16:04.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily close < 1 day ago low + ( 0.1 * daily avg true range( 14 ) )
    group_path: root/group[cash|all]
3. [Disabled] daily high < 1 day ago high
    group_path: root/group[cash|all]
4. [Disabled] daily avg true range( 3 ) > daily avg true range( 14 )
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] daily high / daily open < 1.01
    group_path: root/group[cash|all]
7. [Enabled] daily avg true range( 1 ) > daily avg true range( 14 )
    group_path: root/group[cash|all]
8. [Enabled] ( daily close - daily low ) / ( daily high - daily low ) > 0.4
    group_path: root/group[cash|all]
9. [Enabled] ( daily close - daily low ) / ( daily high - daily low ) < 0.7
    group_path: root/group[cash|all]
10. [Enabled] daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) )
    group_path: root/group[cash|all]
11. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
12. [Disabled] daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) )
    group_path: root/group[cash|all]
13. [Enabled] ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 crossed below -0.01
    group_path: root/group[cash|all]
14. [Enabled] ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 > -0.015
    group_path: root/group[cash|all]
15. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
16. [Disabled] daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) )
    group_path: root/group[cash|all]
17. [Enabled] ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 crossed above 0.02
    group_path: root/group[cash|all]
18. [Disabled] ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 < 0.015
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash (  (  daily close /  1 day ago close ) /  ( rs:'nifty' daily close / rs:'nifty' 1 day ago close ) -  1 >  0.02 and(  1 day ago  close /  2 day ago  close ) /  ( rs:'nifty' 1 day ago  close / rs:'nifty' 2 day ago  close ) -  1 <=  0.02 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily close < 1 day ago low + ( 0.1 * daily avg true range( 14 ) ) | Inequality test: left expression must be strictly less than right. ATR measures smoothed true range (volatility), not direction. |
| 2 | 3 | Disabled | root/group[cash\|all] | daily high < 1 day ago high | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 3 | 4 | Disabled | root/group[cash\|all] | daily avg true range( 3 ) > daily avg true range( 14 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. ATR measures smoothed true range (volatility), not direction. |
| 4 | 6 | Enabled | root/group[cash\|all] | daily high / daily open < 1.01 | Inequality test: left expression must be strictly less than right. |
| 5 | 7 | Enabled | root/group[cash\|all] | daily avg true range( 1 ) > daily avg true range( 14 ) | Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. |
| 6 | 8 | Enabled | root/group[cash\|all] | ( daily close - daily low ) / ( daily high - daily low ) > 0.4 | Inequality test: left expression must be strictly greater than right. |
| 7 | 9 | Enabled | root/group[cash\|all] | ( daily close - daily low ) / ( daily high - daily low ) < 0.7 | Inequality test: left expression must be strictly less than right. |
| 8 | 10 | Enabled | root/group[cash\|all] | daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) ) | Inequality test: left expression must be strictly less than right. ATR measures smoothed true range (volatility), not direction. min(N, series) is the lowest value of series over N bars. |
| 9 | 12 | Disabled | root/group[cash\|all] | daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. ATR measures smoothed true range (volatility), not direction. min(N, series) is the lowest value of series over N bars. |
| 10 | 13 | Enabled | root/group[cash\|all] | ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 crossed below -0.01 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). |
| 11 | 14 | Enabled | root/group[cash\|all] | ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 > -0.015 | Inequality test: left expression must be strictly greater than right. |
| 12 | 16 | Disabled | root/group[cash\|all] | daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. ATR measures smoothed true range (volatility), not direction. min(N, series) is the lowest value of series over N bars. |
| 13 | 17 | Enabled | root/group[cash\|all] | ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 crossed above 0.02 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). |
| 14 | 18 | Disabled | root/group[cash\|all] | ( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 < 0.015 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **9** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily close < 1 day ago low + ( 0.1 * daily avg true range( 14 ) )` — Inequality test: left expression must be strictly less than right. ATR measures smoothed true range (volatility), not direction.
- **#6** `daily high / daily open < 1.01` — Inequality test: left expression must be strictly less than right.
- **#7** `daily avg true range( 1 ) > daily avg true range( 14 )` — Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction.
- **#8** `( daily close - daily low ) / ( daily high - daily low ) > 0.4` — Inequality test: left expression must be strictly greater than right.
- **#9** `( daily close - daily low ) / ( daily high - daily low ) < 0.7` — Inequality test: left expression must be strictly less than right.
- **#10** `daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) )` — Inequality test: left expression must be strictly less than right. ATR measures smoothed true range (volatility), not direction. min(N, series) is the lowest value of series over N bars.
- **#13** `( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 crossed below -0.01` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar).
- **#14** `( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 > -0.015` — Inequality test: left expression must be strictly greater than right.
- **#17** `( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 crossed above 0.02` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar).

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **5** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily high < 1 day ago high`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `daily avg true range( 3 ) > daily avg true range( 14 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. ATR measures smoothed true range (volatility), not direction.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. ATR measures smoothed true range (volatility), not direction. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `daily close < 1 day ago min( 3 ,  daily low ) + ( 0.1 * 1 day ago avg true range( 14 ) )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. ATR measures smoothed true range (volatility), not direction. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #18
- **Condition (verbatim):** `( daily close / 1 day ago close ) / ( daily close / 1 day ago close ) - 1 < 0.015`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 22 time(s) in the expression tree
- `low` — appears 8 time(s) in the expression tree
- `avg true range` — appears 8 time(s) in the expression tree
- `high` — appears 5 time(s) in the expression tree
- `min` — appears 3 time(s) in the expression tree
- `open` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 8 occurrence(s)
- `/` — 7 occurrence(s)
- `+` — 4 occurrence(s)
- `>` — 4 occurrence(s)
- `-` — 4 occurrence(s)
- `crossed below` — 1 occurrence(s)
- `crossed above` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Momentum, Volatility.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **9** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **5** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volatility, Momentum
- **Tags:** universe:nifty-200, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

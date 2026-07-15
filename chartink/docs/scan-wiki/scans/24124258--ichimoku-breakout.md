---
scan_id: 24124258
scan_name: Ichimoku Breakout
source_url: https://chartink.com/screener/ichimoku-breakout-208
market: Indian equities
horizon: "Swing"
classification: ["Moving average","Momentum"]
tags: ["universe:nifty-200","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 20
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# Ichimoku Breakout

## Source

- Chartink URL: https://chartink.com/screener/ichimoku-breakout-208
- Scan ID: `24124258`
- Slug: `ichimoku-breakout-208`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2025-10-11T12:12:48.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24124258.json](../source-snapshots/24124258.json)
- Text snapshot: [source-snapshots/24124258.txt](../source-snapshots/24124258.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **20** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Moving average, Momentum**.

The active tests, in captured order:
- daily close > 26 days ago close
- daily close > 25 days ago close
- daily close > 24 days ago close
- daily close > 23 days ago close
- daily close > 22 days ago close
- daily close > 21 days ago close
- daily close > 20 days ago close
- daily close > 19 days ago close
- daily close > 18 days ago close
- daily close > 17 days ago close
- daily close > 16 days ago close
- daily close > 15 days ago close
- daily close > 14 days ago close
- daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku base line( 9 ,  26 ,  52 )
- daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku span a( 9 ,  26 ,  52 )
- daily ichimoku base line( 9 ,  26 ,  52 ) > daily ichimoku span a( 9 ,  26 ,  52 )
- daily ichimoku span a( 9 ,  26 ,  52 ) > daily ichimoku span b( 9 ,  26 ,  52 )
- daily ichimoku conversion line( 9 ,  26 ,  52 ) crossed above daily ichimoku base line( 9 ,  26 ,  52 )
- daily ichimoku span a( 9 ,  26 ,  52 ) crossed above daily ichimoku span b( 9 ,  26 ,  52 )
- daily close crossed above 26 days ago close

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Ichimoku Breakout
Scan id: 24124258
Slug: ichimoku-breakout-208
Source URL: https://chartink.com/screener/ichimoku-breakout-208
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-10-11T12:12:48.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily close > 26 days ago close
    group_path: root/group[cash|all]
3. [Enabled] daily close > 25 days ago close
    group_path: root/group[cash|all]
4. [Enabled] daily close > 24 days ago close
    group_path: root/group[cash|all]
5. [Enabled] daily close > 23 days ago close
    group_path: root/group[cash|all]
6. [Enabled] daily close > 22 days ago close
    group_path: root/group[cash|all]
7. [Enabled] daily close > 21 days ago close
    group_path: root/group[cash|all]
8. [Enabled] daily close > 20 days ago close
    group_path: root/group[cash|all]
9. [Enabled] daily close > 19 days ago close
    group_path: root/group[cash|all]
10. [Enabled] daily close > 18 days ago close
    group_path: root/group[cash|all]
11. [Enabled] daily close > 17 days ago close
    group_path: root/group[cash|all]
12. [Enabled] daily close > 16 days ago close
    group_path: root/group[cash|all]
13. [Enabled] daily close > 15 days ago close
    group_path: root/group[cash|all]
14. [Enabled] daily close > 14 days ago close
    group_path: root/group[cash|all]
15. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
16. [Enabled] daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku base line( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
17. [Enabled] daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku span a( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
18. [Enabled] daily ichimoku base line( 9 ,  26 ,  52 ) > daily ichimoku span a( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
19. [Enabled] daily ichimoku span a( 9 ,  26 ,  52 ) > daily ichimoku span b( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
20. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
21. [Enabled] daily ichimoku conversion line( 9 ,  26 ,  52 ) crossed above daily ichimoku base line( 9 ,  26 ,  52 )
    group_path: root/group[cash|any]
22. [Enabled] daily ichimoku span a( 9 ,  26 ,  52 ) crossed above daily ichimoku span b( 9 ,  26 ,  52 )
    group_path: root/group[cash|any]
23. [Enabled] daily close crossed above 26 days ago close
    group_path: root/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( daily close > 26 days ago close and daily close > 25 days ago close and daily close > 24 days ago close and daily close > 23 days ago close and daily close > 22 days ago close and daily close > 21 days ago close and daily close > 20 days ago close and daily close > 19 days ago close and daily close > 18 days ago close and daily close > 17 days ago close and daily close > 16 days ago close and daily close > 15 days ago close and daily close > 14 days ago close ) ) and( cash ( daily ichimoku conversion line( 9 , 26 , 52 ) > daily ichimoku base line( 9 , 26 , 52 ) and daily ichimoku conversion line( 9 , 26 , 52 ) > daily ichimoku span a( 9 , 26 , 52 ) and daily ichimoku base line( 9 , 26 , 52 ) > daily ichimoku span a( 9 , 26 , 52 ) and daily ichimoku span a( 9 , 26 , 52 ) > daily ichimoku span b( 9 , 26 , 52 ) ) ) and( cash ( daily ichimoku conversion line( 9 , 26 , 52 ) > daily ichimoku base line( 9 , 26 , 52 ) and 1 day ago  ichimoku conversion line( 9 , 26 , 52 ) <= 1 day ago  ichimoku base line( 9 , 26 , 52 ) or daily ichimoku span a( 9 , 26 , 52 ) > daily ichimoku span b( 9 , 26 , 52 ) and 1 day ago  ichimoku span a( 9 , 26 , 52 ) <= 1 day ago  ichimoku span b( 9 , 26 , 52 ) or daily close > 26 days ago close and 1 day ago  close <= 27 days ago  close ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily close > 26 days ago close | Inequality test: left expression must be strictly greater than right. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily close > 25 days ago close | Inequality test: left expression must be strictly greater than right. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily close > 24 days ago close | Inequality test: left expression must be strictly greater than right. |
| 4 | 5 | Enabled | root/group[cash\|all] | daily close > 23 days ago close | Inequality test: left expression must be strictly greater than right. |
| 5 | 6 | Enabled | root/group[cash\|all] | daily close > 22 days ago close | Inequality test: left expression must be strictly greater than right. |
| 6 | 7 | Enabled | root/group[cash\|all] | daily close > 21 days ago close | Inequality test: left expression must be strictly greater than right. |
| 7 | 8 | Enabled | root/group[cash\|all] | daily close > 20 days ago close | Inequality test: left expression must be strictly greater than right. |
| 8 | 9 | Enabled | root/group[cash\|all] | daily close > 19 days ago close | Inequality test: left expression must be strictly greater than right. |
| 9 | 10 | Enabled | root/group[cash\|all] | daily close > 18 days ago close | Inequality test: left expression must be strictly greater than right. |
| 10 | 11 | Enabled | root/group[cash\|all] | daily close > 17 days ago close | Inequality test: left expression must be strictly greater than right. |
| 11 | 12 | Enabled | root/group[cash\|all] | daily close > 16 days ago close | Inequality test: left expression must be strictly greater than right. |
| 12 | 13 | Enabled | root/group[cash\|all] | daily close > 15 days ago close | Inequality test: left expression must be strictly greater than right. |
| 13 | 14 | Enabled | root/group[cash\|all] | daily close > 14 days ago close | Inequality test: left expression must be strictly greater than right. |
| 14 | 16 | Enabled | root/group[cash\|all] | daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku base line( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 15 | 17 | Enabled | root/group[cash\|all] | daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku span a( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 16 | 18 | Enabled | root/group[cash\|all] | daily ichimoku base line( 9 ,  26 ,  52 ) > daily ichimoku span a( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 17 | 19 | Enabled | root/group[cash\|all] | daily ichimoku span a( 9 ,  26 ,  52 ) > daily ichimoku span b( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 18 | 21 | Enabled | root/group[cash\|any] | daily ichimoku conversion line( 9 ,  26 ,  52 ) crossed above daily ichimoku base line( 9 ,  26 ,  52 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 19 | 22 | Enabled | root/group[cash\|any] | daily ichimoku span a( 9 ,  26 ,  52 ) crossed above daily ichimoku span b( 9 ,  26 ,  52 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 20 | 23 | Enabled | root/group[cash\|any] | daily close crossed above 26 days ago close | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **20** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily close > 26 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#3** `daily close > 25 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#4** `daily close > 24 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily close > 23 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily close > 22 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#7** `daily close > 21 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#8** `daily close > 20 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#9** `daily close > 19 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#10** `daily close > 18 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#11** `daily close > 17 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#12** `daily close > 16 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#13** `daily close > 15 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#14** `daily close > 14 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#16** `daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku base line( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#17** `daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku span a( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#18** `daily ichimoku base line( 9 ,  26 ,  52 ) > daily ichimoku span a( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#19** `daily ichimoku span a( 9 ,  26 ,  52 ) > daily ichimoku span b( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#21** `daily ichimoku conversion line( 9 ,  26 ,  52 ) crossed above daily ichimoku base line( 9 ,  26 ,  52 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#22** `daily ichimoku span a( 9 ,  26 ,  52 ) crossed above daily ichimoku span b( 9 ,  26 ,  52 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#23** `daily close crossed above 26 days ago close` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar).

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
- `close` — appears 28 time(s) in the expression tree
- `ichimoku span a` — appears 4 time(s) in the expression tree
- `ichimoku conversion line` — appears 3 time(s) in the expression tree
- `ichimoku base line` — appears 3 time(s) in the expression tree
- `ichimoku span b` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 17 occurrence(s)
- `crossed above` — 3 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `14_days_ago`, `15_days_ago`, `16_days_ago`, `17_days_ago`, `18_days_ago`, `19_days_ago`, `20_days_ago`, `21_days_ago`, `22_days_ago`, `23_days_ago`, `24_days_ago`, `25_days_ago`, `26_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Moving average, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **20** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average, Momentum
- **Tags:** universe:nifty-200, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

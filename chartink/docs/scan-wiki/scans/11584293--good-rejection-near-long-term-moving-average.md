---
scan_id: 11584293
scan_name: good rejection near long term moving average
source_url: https://chartink.com/screener/good-rejection-near-long-term-moving-average
market: Indian equities
horizon: Swing
classification: ["Moving average", "Trend following", "Volume/delivery", "Multi-factor"]
tags: ["long-bias", "universe:futures", "indicator:rsi", "indicator:ichimoku", "indicator:ema", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 12
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Moving average
---

# good rejection near long term moving average

## Source

- Chartink URL: https://chartink.com/screener/good-rejection-near-long-term-moving-average
- Scan ID: `11584293`
- Slug: `good-rejection-near-long-term-moving-average`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-04-26T13:58:25.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11584293.json](../source-snapshots/11584293.json)
- Text snapshot: [source-snapshots/11584293.txt](../source-snapshots/11584293.txt)

## What this scan is for

This scan, titled "good rejection near long term moving average", appears designed to screen Indian equities in the **futures** universe using **12 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Moving average, Trend following, Volume/delivery, Multi-factor**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: good rejection near long term moving average
Scan id: 11584293
Slug: good-rejection-near-long-term-moving-average
Source URL: https://chartink.com/screener/good-rejection-near-long-term-moving-average
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-26T13:58:25.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] ( daily least - daily low ) / ( daily high - daily low ) > 0.5
2. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Enabled] daily low / daily ema( close ,  233 ) > 0.99
    group_path: root/group[cash|all]
4. [Enabled] daily low / daily ema( close ,  233 ) < 1.01
    group_path: root/group[cash|all]
5. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
6. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|any]/group[cash|all])
7. [Enabled] daily low / daily ichimoku conversion line( 9 ,  26 ,  52 ) > 0.99
    group_path: root/group[cash|any]/group[cash|all]
8. [Enabled] daily low / daily ichimoku conversion line( 9 ,  26 ,  52 ) < 1.01
    group_path: root/group[cash|any]/group[cash|all]
9. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|any]/group[cash|all])
10. [Enabled] daily low / daily ichimoku base line( 9 ,  26 ,  52 ) > 0.99
    group_path: root/group[cash|any]/group[cash|all]
11. [Enabled] daily low / daily ichimoku base line( 9 ,  26 ,  52 ) < 1.01
    group_path: root/group[cash|any]/group[cash|all]
12. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
13. [Enabled] daily ichimoku span a( 9 ,  26 ,  52 ) > daily ichimoku span b( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
14. [Enabled] daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku base line( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
15. [Enabled] daily ichimoku base line( 9 ,  26 ,  52 ) > daily ichimoku cloud top( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
16. [Enabled] daily close > daily ichimoku cloud top( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
17. [Enabled] daily low < daily ichimoku base line( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
18. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
19. [Disabled] daily HLC3 > 1 day ago sma( close ,  5 ) * 1.01
    group_path: root/group[cash|all]
20. [Enabled] daily buy orders quantity ratio > 1
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( ( cash ( ( cash ( latest low / latest ichimoku conversion line( 9 , 26 , 52 ) > 0.99 and latest low / latest ichimoku conversion line( 9 , 26 , 52 ) < 1.01 ) ) or( cash ( latest low / latest ichimoku base line( 9 , 26 , 52 ) > 0.99 and latest low / latest ichimoku base line( 9 , 26 , 52 ) < 1.01 ) ) ) ) and( cash ( latest ichimoku span a( 9 , 26 , 52 ) > latest ichimoku span b( 9 , 26 , 52 ) and latest ichimoku conversion line( 9 , 26 , 52 ) > latest ichimoku base line( 9 , 26 , 52 ) and latest ichimoku base line( 9 , 26 , 52 ) > latest ichimoku cloud top( 9 , 26 , 52 ) and latest close > latest ichimoku cloud top( 9 , 26 , 52 ) and latest low < latest ichimoku base line( 9 , 26 , 52 ) ) ) and( cash ( latest "buy orders quantity / sell orders quantity" > 1 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | ( daily least - daily low ) / ( daily high - daily low ) > 0.5 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 2 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 3 | Enabled | daily low / daily ema( close ,  233 ) > 0.99 | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 4 | Enabled | daily low / daily ema( close ,  233 ) < 1.01 | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. |
| 5 | Enabled | [GROUP segment=cash join=any combination=passes measurevalue=default] | Nested group over segment **cash** with join **any** (combination=passes). Group status=Enabled. |
| 6 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 7 | Enabled | daily low / daily ichimoku conversion line( 9 ,  26 ,  52 ) > 0.99 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 8 | Enabled | daily low / daily ichimoku conversion line( 9 ,  26 ,  52 ) < 1.01 | Inequality test: left expression must be strictly less than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 9 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 10 | Enabled | daily low / daily ichimoku base line( 9 ,  26 ,  52 ) > 0.99 | Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 11 | Enabled | daily low / daily ichimoku base line( 9 ,  26 ,  52 ) < 1.01 | Inequality test: left expression must be strictly less than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 12 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 13 | Enabled | daily ichimoku span a( 9 ,  26 ,  52 ) > daily ichimoku span b( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 14 | Enabled | daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku base line( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 15 | Enabled | daily ichimoku base line( 9 ,  26 ,  52 ) > daily ichimoku cloud top( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 16 | Enabled | daily close > daily ichimoku cloud top( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 17 | Enabled | daily low < daily ichimoku base line( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly less than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. |
| 18 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 19 | Disabled | daily HLC3 > 1 day ago sma( close ,  5 ) * 1.01 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. |
| 20 | Enabled | daily buy orders quantity ratio > 1 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **12** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `daily low / daily ema( close ,  233 ) > 0.99` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#4** `daily low / daily ema( close ,  233 ) < 1.01` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field.
- **#7** `daily low / daily ichimoku conversion line( 9 ,  26 ,  52 ) > 0.99` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#8** `daily low / daily ichimoku conversion line( 9 ,  26 ,  52 ) < 1.01` — Inequality test: left expression must be strictly less than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#10** `daily low / daily ichimoku base line( 9 ,  26 ,  52 ) > 0.99` — Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#11** `daily low / daily ichimoku base line( 9 ,  26 ,  52 ) < 1.01` — Inequality test: left expression must be strictly less than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#13** `daily ichimoku span a( 9 ,  26 ,  52 ) > daily ichimoku span b( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#14** `daily ichimoku conversion line( 9 ,  26 ,  52 ) > daily ichimoku base line( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#15** `daily ichimoku base line( 9 ,  26 ,  52 ) > daily ichimoku cloud top( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#16** `daily close > daily ichimoku cloud top( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#17** `daily low < daily ichimoku base line( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly less than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.
- **#20** `daily buy orders quantity ratio > 1` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `( daily least - daily low ) / ( daily high - daily low ) > 0.5`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #19
- **Condition (verbatim):** `daily HLC3 > 1 day ago sma( close ,  5 ) * 1.01`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `low` — appears 9 time(s) in the expression tree
- `ichimoku base line` — appears 5 time(s) in the expression tree
- `close` — appears 4 time(s) in the expression tree
- `ichimoku conversion line` — appears 3 time(s) in the expression tree
- `ema` — appears 2 time(s) in the expression tree
- `ichimoku cloud top` — appears 2 time(s) in the expression tree
- `custom_indicator_4583` — appears 2 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `least` — appears 1 time(s) in the expression tree
- `open` — appears 1 time(s) in the expression tree
- `ichimoku span a` — appears 1 time(s) in the expression tree
- `ichimoku span b` — appears 1 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree
- `buy orders quantity ratio` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 10 occurrence(s)
- `/` — 7 occurrence(s)
- `<` — 4 occurrence(s)
- `*` — 1 occurrence(s)

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
- **Method context:** Moving average, Trend following, Volume/delivery, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **12** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Moving average, Trend following, Volume/delivery, Multi-factor
- **Tags:** long-bias, universe:futures, indicator:rsi, indicator:ichimoku, indicator:ema, indicator:sma, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 2615077
scan_name: rsi divergence 2
source_url: https://chartink.com/screener/rsi-divergence-2-93
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery","Oscillator"]
tags: ["universe:cash","indicator:volume","indicator:rsi","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 15
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: any
primary_classification: Volume/delivery
---

# rsi divergence 2

## Source

- Chartink URL: https://chartink.com/screener/rsi-divergence-2-93
- Scan ID: `2615077`
- Slug: `rsi-divergence-2-93`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-07-29T02:15:53.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2615077.json](../source-snapshots/2615077.json)
- Text snapshot: [source-snapshots/2615077.txt](../source-snapshots/2615077.txt)

## What this scan is for

This is a **swing** screen over **cash** with **15** active leaf condition(s) under root join **any**.
Its method labels are derived only from active expressions: **Volume/delivery, Oscillator**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 1000000000
- daily low < 6 days ago low * 1.001
- daily low > 6 days ago low * 0.999
- 1 day ago min( 4 ,  daily low ) > 6 days ago low
- daily rsi( 14 ) > 6 days ago rsi( 14 ) * 1.1
- 1 day ago close * 1 day ago volume > 1000000000
- daily low < 7 days ago low * 1.001
- daily low > 7 days ago low * 0.999
- 1 day ago min( 5 ,  daily low ) > 7 days ago low
- daily rsi( 14 ) > 7 days ago rsi( 14 ) * 1.1
- 1 day ago close * 1 day ago volume > 1000000000
- daily low < 8 days ago low * 1.001
- daily low > 8 days ago low * 0.999
- 1 day ago min( 6 ,  daily low ) > 8 days ago low
- daily rsi( 14 ) > 8 days ago rsi( 14 ) * 1.1

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: rsi divergence 2
Scan id: 2615077
Slug: rsi-divergence-2-93
Source URL: https://chartink.com/screener/rsi-divergence-2-93
Root universe/segment: cash
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-29T02:15:53.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 1000000000
    group_path: root/group[cash|all]
3. [Enabled] daily low < 6 days ago low * 1.001
    group_path: root/group[cash|all]
4. [Enabled] daily low > 6 days ago low * 0.999
    group_path: root/group[cash|all]
5. [Enabled] 1 day ago min( 4 ,  daily low ) > 6 days ago low
    group_path: root/group[cash|all]
6. [Enabled] daily rsi( 14 ) > 6 days ago rsi( 14 ) * 1.1
    group_path: root/group[cash|all]
7. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Enabled] 1 day ago close * 1 day ago volume > 1000000000
    group_path: root/group[cash|all]
9. [Enabled] daily low < 7 days ago low * 1.001
    group_path: root/group[cash|all]
10. [Enabled] daily low > 7 days ago low * 0.999
    group_path: root/group[cash|all]
11. [Enabled] 1 day ago min( 5 ,  daily low ) > 7 days ago low
    group_path: root/group[cash|all]
12. [Enabled] daily rsi( 14 ) > 7 days ago rsi( 14 ) * 1.1
    group_path: root/group[cash|all]
13. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Enabled] 1 day ago close * 1 day ago volume > 1000000000
    group_path: root/group[cash|all]
15. [Enabled] daily low < 8 days ago low * 1.001
    group_path: root/group[cash|all]
16. [Enabled] daily low > 8 days ago low * 0.999
    group_path: root/group[cash|all]
17. [Enabled] 1 day ago min( 6 ,  daily low ) > 8 days ago low
    group_path: root/group[cash|all]
18. [Enabled] daily rsi( 14 ) > 8 days ago rsi( 14 ) * 1.1
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 1000000000 and latest low < 6 days ago low * 1.001 and latest low > 6 days ago low * 0.999 and 1 day ago min( 4 , latest low ) > 6 days ago low and latest rsi( 14 ) > 6 days ago rsi( 14 ) * 1.1 ) ) or( cash ( 1 day ago close * 1 day ago volume > 1000000000 and latest low < 7 days ago low * 1.001 and latest low > 7 days ago low * 0.999 and 1 day ago min( 5 , latest low ) > 7 days ago low and latest rsi( 14 ) > 7 days ago rsi( 14 ) * 1.1 ) ) or( cash ( 1 day ago close * 1 day ago volume > 1000000000 and latest low < 8 days ago low * 1.001 and latest low > 8 days ago low * 0.999 and 1 day ago min( 6 , latest low ) > 8 days ago low and latest rsi( 14 ) > 8 days ago rsi( 14 ) * 1.1 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 1000000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily low < 6 days ago low * 1.001 | Inequality test: left expression must be strictly less than right. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily low > 6 days ago low * 0.999 | Inequality test: left expression must be strictly greater than right. |
| 4 | 5 | Enabled | root/group[cash\|all] | 1 day ago min( 4 ,  daily low ) > 6 days ago low | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |
| 5 | 6 | Enabled | root/group[cash\|all] | daily rsi( 14 ) > 6 days ago rsi( 14 ) * 1.1 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 6 | 8 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 1000000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 7 | 9 | Enabled | root/group[cash\|all] | daily low < 7 days ago low * 1.001 | Inequality test: left expression must be strictly less than right. |
| 8 | 10 | Enabled | root/group[cash\|all] | daily low > 7 days ago low * 0.999 | Inequality test: left expression must be strictly greater than right. |
| 9 | 11 | Enabled | root/group[cash\|all] | 1 day ago min( 5 ,  daily low ) > 7 days ago low | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |
| 10 | 12 | Enabled | root/group[cash\|all] | daily rsi( 14 ) > 7 days ago rsi( 14 ) * 1.1 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 11 | 14 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 1000000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 12 | 15 | Enabled | root/group[cash\|all] | daily low < 8 days ago low * 1.001 | Inequality test: left expression must be strictly less than right. |
| 13 | 16 | Enabled | root/group[cash\|all] | daily low > 8 days ago low * 0.999 | Inequality test: left expression must be strictly greater than right. |
| 14 | 17 | Enabled | root/group[cash\|all] | 1 day ago min( 6 ,  daily low ) > 8 days ago low | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |
| 15 | 18 | Enabled | root/group[cash\|all] | daily rsi( 14 ) > 8 days ago rsi( 14 ) * 1.1 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **15** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 1000000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `daily low < 6 days ago low * 1.001` — Inequality test: left expression must be strictly less than right.
- **#4** `daily low > 6 days ago low * 0.999` — Inequality test: left expression must be strictly greater than right.
- **#5** `1 day ago min( 4 ,  daily low ) > 6 days ago low` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.
- **#6** `daily rsi( 14 ) > 6 days ago rsi( 14 ) * 1.1` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#8** `1 day ago close * 1 day ago volume > 1000000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#9** `daily low < 7 days ago low * 1.001` — Inequality test: left expression must be strictly less than right.
- **#10** `daily low > 7 days ago low * 0.999` — Inequality test: left expression must be strictly greater than right.
- **#11** `1 day ago min( 5 ,  daily low ) > 7 days ago low` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.
- **#12** `daily rsi( 14 ) > 7 days ago rsi( 14 ) * 1.1` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#14** `1 day ago close * 1 day ago volume > 1000000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#15** `daily low < 8 days ago low * 1.001` — Inequality test: left expression must be strictly less than right.
- **#16** `daily low > 8 days ago low * 0.999` — Inequality test: left expression must be strictly greater than right.
- **#17** `1 day ago min( 6 ,  daily low ) > 8 days ago low` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.
- **#18** `daily rsi( 14 ) > 8 days ago rsi( 14 ) * 1.1` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.

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
- `low` — appears 18 time(s) in the expression tree
- `rsi` — appears 6 time(s) in the expression tree
- `close` — appears 3 time(s) in the expression tree
- `volume` — appears 3 time(s) in the expression tree
- `min` — appears 3 time(s) in the expression tree

### Operators observed
- `*` — 12 occurrence(s)
- `>` — 12 occurrence(s)
- `<` — 3 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **cash**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `6_days_ago`, `7_days_ago`, `8_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **15** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery, Oscillator
- **Tags:** universe:cash, indicator:volume, indicator:rsi, timeframe:daily
- **Root universe:** cash
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 2591776
scan_name: SBIN SELL
source_url: https://chartink.com/screener/divergence-rsi-16
market: Indian equities
horizon: "Swing"
classification: ["Moving average","Volume/delivery","Oscillator"]
tags: ["universe:11","indicator:sma","indicator:volume","indicator:mfi","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 3
needs_review_filter_count: 0
root_segment: "11"
root_join: any
primary_classification: Moving average
---

# SBIN SELL

## Source

- Chartink URL: https://chartink.com/screener/divergence-rsi-16
- Scan ID: `2591776`
- Slug: `divergence-rsi-16`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-07-26T03:42:38.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2591776.json](../source-snapshots/2591776.json)
- Text snapshot: [source-snapshots/2591776.txt](../source-snapshots/2591776.txt)

## What this scan is for

This is a **swing** screen over **11** with **6** active leaf condition(s) under root join **any**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Oscillator**.

The active tests, in captured order:
- daily close > 1 day ago close * 1.01
- 1 day ago close > 2 days ago close * 1.01
- 2 days ago close > 3 days ago close * 1.01
- 3 days ago close > 4 days ago close * 1.01
- daily sma( close ,  5 ) < daily sma( close ,  20 )
- daily mfi( 14 ) > 80

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: SBIN SELL
Scan id: 2591776
Slug: divergence-rsi-16
Source URL: https://chartink.com/screener/divergence-rsi-16
Root universe/segment: 11
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-26T03:42:38.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=11 join=all combination=passes measurevalue=default]  (path: root/group[11|all])
2. [Enabled] daily close > 1 day ago close * 1.01
    group_path: root/group[11|all]
3. [Enabled] 1 day ago close > 2 days ago close * 1.01
    group_path: root/group[11|all]
4. [Enabled] 2 days ago close > 3 days ago close * 1.01
    group_path: root/group[11|all]
5. [Enabled] 3 days ago close > 4 days ago close * 1.01
    group_path: root/group[11|all]
6. [Enabled] daily sma( close ,  5 ) < daily sma( close ,  20 )
    group_path: root/group[11|all]
7. [Enabled] [GROUP segment=11 join=all combination=passes measurevalue=default]  (path: root/group[11|all])
8. [Enabled] daily mfi( 14 ) > 80
    group_path: root/group[11|all]
9. [Disabled] 1 day ago rsi( 14 ) < 2 days ago rsi( 14 )
    group_path: root/group[11|all]
10. [Disabled] 3 days ago rsi( 14 ) < 3 days ago rsi( 14 )
    group_path: root/group[11|all]
11. [Disabled] 3 days ago rsi( 14 ) < 4 days ago rsi( 14 )
    group_path: root/group[11|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( watchlist ( ( watchlist ( latest mfi( 14 ) > 80 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[11\|all] | daily close > 1 day ago close * 1.01 | Inequality test: left expression must be strictly greater than right. |
| 2 | 3 | Enabled | root/group[11\|all] | 1 day ago close > 2 days ago close * 1.01 | Inequality test: left expression must be strictly greater than right. |
| 3 | 4 | Enabled | root/group[11\|all] | 2 days ago close > 3 days ago close * 1.01 | Inequality test: left expression must be strictly greater than right. |
| 4 | 5 | Enabled | root/group[11\|all] | 3 days ago close > 4 days ago close * 1.01 | Inequality test: left expression must be strictly greater than right. |
| 5 | 6 | Enabled | root/group[11\|all] | daily sma( close ,  5 ) < daily sma( close ,  20 ) | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 6 | 8 | Enabled | root/group[11\|all] | daily mfi( 14 ) > 80 | Inequality test: left expression must be strictly greater than right. |
| 7 | 9 | Disabled | root/group[11\|all] | 1 day ago rsi( 14 ) < 2 days ago rsi( 14 ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 8 | 10 | Disabled | root/group[11\|all] | 3 days ago rsi( 14 ) < 3 days ago rsi( 14 ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 9 | 11 | Disabled | root/group[11\|all] | 3 days ago rsi( 14 ) < 4 days ago rsi( 14 ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily close > 1 day ago close * 1.01` — Inequality test: left expression must be strictly greater than right.
- **#3** `1 day ago close > 2 days ago close * 1.01` — Inequality test: left expression must be strictly greater than right.
- **#4** `2 days ago close > 3 days ago close * 1.01` — Inequality test: left expression must be strictly greater than right.
- **#5** `3 days ago close > 4 days ago close * 1.01` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily sma( close ,  5 ) < daily sma( close ,  20 )` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#8** `daily mfi( 14 ) > 80` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **3** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #9
- **Condition (verbatim):** `1 day ago rsi( 14 ) < 2 days ago rsi( 14 )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `3 days ago rsi( 14 ) < 3 days ago rsi( 14 )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `3 days ago rsi( 14 ) < 4 days ago rsi( 14 )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 8 time(s) in the expression tree
- `rsi` — appears 6 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `mfi` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 5 occurrence(s)
- `*` — 4 occurrence(s)
- `<` — 4 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **11**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`, `4_days_ago`, `5_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **11**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Moving average, Volume/delivery, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **11**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **3** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average, Volume/delivery, Oscillator
- **Tags:** universe:11, indicator:sma, indicator:volume, indicator:mfi, timeframe:daily
- **Root universe:** 11
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

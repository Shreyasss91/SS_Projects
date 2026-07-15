---
scan_id: 2587351
scan_name: divergence_priceriseexhuast
source_url: https://chartink.com/screener/divergence-priceriseexhuast
market: Indian equities
horizon: "Swing"
classification: ["Oscillator","Volume/delivery"]
tags: ["universe:futures","indicator:rsi","indicator:volume","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 10
disabled_filter_count: 8
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Oscillator
---

# divergence_priceriseexhuast

## Source

- Chartink URL: https://chartink.com/screener/divergence-priceriseexhuast
- Scan ID: `2587351`
- Slug: `divergence-priceriseexhuast`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-07-25T12:42:47.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2587351.json](../source-snapshots/2587351.json)
- Text snapshot: [source-snapshots/2587351.txt](../source-snapshots/2587351.txt)

## What this scan is for

This is a **swing** screen over **futures** with **10** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Oscillator, Volume/delivery**.

The active tests, in captured order:
- 1 day ago close > 2 days ago close
- 2 days ago close > 3 days ago close
- 3 days ago close > 4 days ago close
- 4 days ago close > 5 days ago close
- 1 day ago rsi( 14 ) > 2 days ago rsi( 14 )
- 2 days ago rsi( 14 ) > 3 days ago rsi( 14 )
- 3 days ago rsi( 14 ) > 4 days ago rsi( 14 )
- 4 days ago rsi( 14 ) > 5 days ago rsi( 14 )
- 1 day ago close * 1 day ago volume > 1000000000
- daily close > 1 day ago close * 1.05

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: divergence_priceriseexhuast
Scan id: 2587351
Slug: divergence-priceriseexhuast
Source URL: https://chartink.com/screener/divergence-priceriseexhuast
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-25T12:42:47.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily close > 1 day ago close
2. [Enabled] 1 day ago close > 2 days ago close
3. [Enabled] 2 days ago close > 3 days ago close
4. [Enabled] 3 days ago close > 4 days ago close
5. [Enabled] 4 days ago close > 5 days ago close
6. [Disabled] 5 days ago close > 6 days ago close
7. [Disabled] 6 days ago close > 7 days ago close
8. [Disabled] 7 days ago close > 8 days ago close
9. [Disabled] daily rsi( 14 ) > 1 day ago rsi( 14 )
10. [Enabled] 1 day ago rsi( 14 ) > 2 days ago rsi( 14 )
11. [Enabled] 2 days ago rsi( 14 ) > 3 days ago rsi( 14 )
12. [Enabled] 3 days ago rsi( 14 ) > 4 days ago rsi( 14 )
13. [Enabled] 4 days ago rsi( 14 ) > 5 days ago rsi( 14 )
14. [Disabled] 5 days ago rsi( 14 ) > 6 days ago rsi( 14 )
15. [Disabled] 6 days ago rsi( 14 ) > 7 days ago rsi( 14 )
16. [Disabled] 7 days ago rsi( 14 ) > 8 days ago rsi( 14 )
17. [Enabled] 1 day ago close * 1 day ago volume > 1000000000
18. [Enabled] daily close > 1 day ago close * 1.05

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( 1 day ago close > 2 days ago close and 2 days ago close > 3 days ago close and 3 days ago close > 4 days ago close and 4 days ago close > 5 days ago close and 1 day ago rsi( 14 ) > 2 days ago rsi( 14 ) and 2 days ago rsi( 14 ) > 3 days ago rsi( 14 ) and 3 days ago rsi( 14 ) > 4 days ago rsi( 14 ) and 4 days ago rsi( 14 ) > 5 days ago rsi( 14 ) and 1 day ago close * 1 day ago volume > 1000000000 and latest close > 1 day ago close * 1.05 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily close > 1 day ago close | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 2 | 2 | Enabled | root | 1 day ago close > 2 days ago close | Inequality test: left expression must be strictly greater than right. |
| 3 | 3 | Enabled | root | 2 days ago close > 3 days ago close | Inequality test: left expression must be strictly greater than right. |
| 4 | 4 | Enabled | root | 3 days ago close > 4 days ago close | Inequality test: left expression must be strictly greater than right. |
| 5 | 5 | Enabled | root | 4 days ago close > 5 days ago close | Inequality test: left expression must be strictly greater than right. |
| 6 | 6 | Disabled | root | 5 days ago close > 6 days ago close | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 7 | 7 | Disabled | root | 6 days ago close > 7 days ago close | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 8 | 8 | Disabled | root | 7 days ago close > 8 days ago close | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 9 | 9 | Disabled | root | daily rsi( 14 ) > 1 day ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 10 | 10 | Enabled | root | 1 day ago rsi( 14 ) > 2 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 11 | 11 | Enabled | root | 2 days ago rsi( 14 ) > 3 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 12 | 12 | Enabled | root | 3 days ago rsi( 14 ) > 4 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 13 | 13 | Enabled | root | 4 days ago rsi( 14 ) > 5 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 14 | 14 | Disabled | root | 5 days ago rsi( 14 ) > 6 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 15 | 15 | Disabled | root | 6 days ago rsi( 14 ) > 7 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 16 | 16 | Disabled | root | 7 days ago rsi( 14 ) > 8 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 17 | 17 | Enabled | root | 1 day ago close * 1 day ago volume > 1000000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 18 | 18 | Enabled | root | daily close > 1 day ago close * 1.05 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **10** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close > 2 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#3** `2 days ago close > 3 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#4** `3 days ago close > 4 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#5** `4 days ago close > 5 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#10** `1 day ago rsi( 14 ) > 2 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#11** `2 days ago rsi( 14 ) > 3 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#12** `3 days ago rsi( 14 ) > 4 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#13** `4 days ago rsi( 14 ) > 5 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#17** `1 day ago close * 1 day ago volume > 1000000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#18** `daily close > 1 day ago close * 1.05` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **8** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily close > 1 day ago close`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `5 days ago close > 6 days ago close`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `6 days ago close > 7 days ago close`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `7 days ago close > 8 days ago close`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `daily rsi( 14 ) > 1 day ago rsi( 14 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `5 days ago rsi( 14 ) > 6 days ago rsi( 14 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #15
- **Condition (verbatim):** `6 days ago rsi( 14 ) > 7 days ago rsi( 14 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `7 days ago rsi( 14 ) > 8 days ago rsi( 14 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 19 time(s) in the expression tree
- `rsi` — appears 16 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 18 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`, `4_days_ago`, `5_days_ago`, `6_days_ago`, `7_days_ago`, `8_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **10** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **8** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Oscillator, Volume/delivery
- **Tags:** universe:futures, indicator:rsi, indicator:volume, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 2588433
scan_name: divergence bearish
source_url: https://chartink.com/screener/divergence-bearish-61
market: Indian equities
horizon: Swing
classification: ["Oscillator", "Volume/delivery"]
tags: ["bias:upward-condition", "universe:futures", "indicator:rsi", "indicator:volume", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 16
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Oscillator
---

# divergence bearish

## Source

- Chartink URL: https://chartink.com/screener/divergence-bearish-61
- Scan ID: `2588433`
- Slug: `divergence-bearish-61`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-07-25T14:50:30.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2588433.json](../source-snapshots/2588433.json)
- Text snapshot: [source-snapshots/2588433.txt](../source-snapshots/2588433.txt)

## What this scan is for

This is a **swing** screen over **futures** with **16** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Oscillator, Volume/delivery**.
The active tests, in captured order, are:
- daily close > 1 day ago close
- 1 day ago close > 2 days ago close
- 2 days ago close > 3 days ago close
- 3 days ago close > 4 days ago close
- daily rsi( 14 ) > 1 day ago rsi( 14 )
- 1 day ago rsi( 14 ) > 2 days ago rsi( 14 )
- 2 days ago rsi( 14 ) > 3 days ago rsi( 14 )
- 3 days ago rsi( 14 ) > 4 days ago rsi( 14 )
- 1 day ago close * 1 day ago volume > 1000000000
- daily high > 1 day ago high * 1.1
- 4 days ago close > 5 days ago close
- 5 days ago close > 6 days ago close
- 6 days ago close > 7 days ago close
- 4 days ago rsi( 14 ) > 5 days ago rsi( 14 )
- 5 days ago rsi( 14 ) > 6 days ago rsi( 14 )
- 6 days ago rsi( 14 ) > 7 days ago rsi( 14 )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: divergence bearish
Scan id: 2588433
Slug: divergence-bearish-61
Source URL: https://chartink.com/screener/divergence-bearish-61
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-25T14:50:30.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily close > 1 day ago close
2. [Enabled] 1 day ago close > 2 days ago close
3. [Enabled] 2 days ago close > 3 days ago close
4. [Enabled] 3 days ago close > 4 days ago close
5. [Enabled] daily rsi( 14 ) > 1 day ago rsi( 14 )
6. [Enabled] 1 day ago rsi( 14 ) > 2 days ago rsi( 14 )
7. [Enabled] 2 days ago rsi( 14 ) > 3 days ago rsi( 14 )
8. [Enabled] 3 days ago rsi( 14 ) > 4 days ago rsi( 14 )
9. [Enabled] 1 day ago close * 1 day ago volume > 1000000000
10. [Enabled] daily high > 1 day ago high * 1.1
11. [Disabled] daily volume > 1 day ago volume * 1.1
12. [Disabled] daily open < 1 day ago close * 1.04
13. [Disabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|all])
14. [Enabled] 4 days ago close > 5 days ago close
    group_path: root/group[futures|all]
15. [Enabled] 5 days ago close > 6 days ago close
    group_path: root/group[futures|all]
16. [Enabled] 6 days ago close > 7 days ago close
    group_path: root/group[futures|all]
17. [Enabled] 4 days ago rsi( 14 ) > 5 days ago rsi( 14 )
    group_path: root/group[futures|all]
18. [Enabled] 5 days ago rsi( 14 ) > 6 days ago rsi( 14 )
    group_path: root/group[futures|all]
19. [Enabled] 6 days ago rsi( 14 ) > 7 days ago rsi( 14 )
    group_path: root/group[futures|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( latest close > 1 day ago close and 1 day ago close > 2 days ago close and 2 days ago close > 3 days ago close and 3 days ago close > 4 days ago close and latest rsi( 14 ) > 1 day ago rsi( 14 ) and 1 day ago rsi( 14 ) > 2 days ago rsi( 14 ) and 2 days ago rsi( 14 ) > 3 days ago rsi( 14 ) and 3 days ago rsi( 14 ) > 4 days ago rsi( 14 ) and 1 day ago close * 1 day ago volume > 1000000000 and latest high > 1 day ago high * 1.1 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily close > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | 1 day ago close > 2 days ago close | Inequality test: left expression must be strictly greater than right. |
| 3 | 3 | Enabled | root | 2 days ago close > 3 days ago close | Inequality test: left expression must be strictly greater than right. |
| 4 | 4 | Enabled | root | 3 days ago close > 4 days ago close | Inequality test: left expression must be strictly greater than right. |
| 5 | 5 | Enabled | root | daily rsi( 14 ) > 1 day ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 6 | 6 | Enabled | root | 1 day ago rsi( 14 ) > 2 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 7 | 7 | Enabled | root | 2 days ago rsi( 14 ) > 3 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 8 | 8 | Enabled | root | 3 days ago rsi( 14 ) > 4 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 9 | 9 | Enabled | root | 1 day ago close * 1 day ago volume > 1000000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 10 | 10 | Enabled | root | daily high > 1 day ago high * 1.1 | Inequality test: left expression must be strictly greater than right. |
| 11 | 11 | Disabled | root | daily volume > 1 day ago volume * 1.1 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |
| 12 | 12 | Disabled | root | daily open < 1 day ago close * 1.04 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 13 | 14 | Enabled | root/group[futures\|all] | 4 days ago close > 5 days ago close | Inequality test: left expression must be strictly greater than right. |
| 14 | 15 | Enabled | root/group[futures\|all] | 5 days ago close > 6 days ago close | Inequality test: left expression must be strictly greater than right. |
| 15 | 16 | Enabled | root/group[futures\|all] | 6 days ago close > 7 days ago close | Inequality test: left expression must be strictly greater than right. |
| 16 | 17 | Enabled | root/group[futures\|all] | 4 days ago rsi( 14 ) > 5 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 17 | 18 | Enabled | root/group[futures\|all] | 5 days ago rsi( 14 ) > 6 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 18 | 19 | Enabled | root/group[futures\|all] | 6 days ago rsi( 14 ) > 7 days ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **16** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily close > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#2** `1 day ago close > 2 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#3** `2 days ago close > 3 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#4** `3 days ago close > 4 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily rsi( 14 ) > 1 day ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#6** `1 day ago rsi( 14 ) > 2 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#7** `2 days ago rsi( 14 ) > 3 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#8** `3 days ago rsi( 14 ) > 4 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#9** `1 day ago close * 1 day ago volume > 1000000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#10** `daily high > 1 day ago high * 1.1` — Inequality test: left expression must be strictly greater than right.
- **#14** `4 days ago close > 5 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#15** `5 days ago close > 6 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#16** `6 days ago close > 7 days ago close` — Inequality test: left expression must be strictly greater than right.
- **#17** `4 days ago rsi( 14 ) > 5 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#18** `5 days ago rsi( 14 ) > 6 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#19** `6 days ago rsi( 14 ) > 7 days ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #11
- **Condition (verbatim):** `daily volume > 1 day ago volume * 1.1`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `daily open < 1 day ago close * 1.04`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 16 time(s) in the expression tree
- `rsi` — appears 14 time(s) in the expression tree
- `volume` — appears 3 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree
- `open` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 17 occurrence(s)
- `*` — 4 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`, `4_days_ago`, `5_days_ago`, `6_days_ago`, `7_days_ago`

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

- Explicit, machine-readable condition tree with **16** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Tags:** bias:upward-condition, universe:futures, indicator:rsi, indicator:volume, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

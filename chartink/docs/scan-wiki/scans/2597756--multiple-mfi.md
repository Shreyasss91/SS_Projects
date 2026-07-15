---
scan_id: 2597756
scan_name: multiple MFI
source_url: https://chartink.com/screener/multiple-mfi-1
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery","Oscillator"]
tags: ["universe:cash","indicator:volume","indicator:mfi","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 5
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# multiple MFI

## Source

- Chartink URL: https://chartink.com/screener/multiple-mfi-1
- Scan ID: `2597756`
- Slug: `multiple-mfi-1`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-07-26T15:59:49.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2597756.json](../source-snapshots/2597756.json)
- Text snapshot: [source-snapshots/2597756.txt](../source-snapshots/2597756.txt)

## What this scan is for

This is a **swing** screen over **cash** with **6** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Oscillator**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 1000000000
- daily mfi( 14 ) > 80
- daily mfi( 21 ) > 80
- daily mfi( 28 ) > 80
- daily mfi( 35 ) > 80
- daily mfi( 42 ) > 80

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: multiple MFI
Scan id: 2597756
Slug: multiple-mfi-1
Source URL: https://chartink.com/screener/multiple-mfi-1
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-26T15:59:49.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close * 1 day ago volume > 1000000000
2. [Enabled] daily mfi( 14 ) > 80
3. [Enabled] daily mfi( 21 ) > 80
4. [Enabled] daily mfi( 28 ) > 80
5. [Enabled] daily mfi( 35 ) > 80
6. [Enabled] daily mfi( 42 ) > 80
7. [Disabled] daily mfi( 14 ) < 40
8. [Disabled] daily mfi( 21 ) < 40
9. [Disabled] daily mfi( 28 ) < 40
10. [Disabled] daily mfi( 35 ) < 40
11. [Disabled] daily mfi( 42 ) < 40

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( 1 day ago close * 1 day ago volume > 1000000000 and latest mfi( 14 ) > 80 and latest mfi( 21 ) > 80 and latest mfi( 28 ) > 80 and latest mfi( 35 ) > 80 and latest mfi( 42 ) > 80 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 1 day ago close * 1 day ago volume > 1000000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 2 | Enabled | root | daily mfi( 14 ) > 80 | Inequality test: left expression must be strictly greater than right. |
| 3 | 3 | Enabled | root | daily mfi( 21 ) > 80 | Inequality test: left expression must be strictly greater than right. |
| 4 | 4 | Enabled | root | daily mfi( 28 ) > 80 | Inequality test: left expression must be strictly greater than right. |
| 5 | 5 | Enabled | root | daily mfi( 35 ) > 80 | Inequality test: left expression must be strictly greater than right. |
| 6 | 6 | Enabled | root | daily mfi( 42 ) > 80 | Inequality test: left expression must be strictly greater than right. |
| 7 | 7 | Disabled | root | daily mfi( 14 ) < 40 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 8 | 8 | Disabled | root | daily mfi( 21 ) < 40 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 9 | 9 | Disabled | root | daily mfi( 28 ) < 40 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 10 | 10 | Disabled | root | daily mfi( 35 ) < 40 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 11 | 11 | Disabled | root | daily mfi( 42 ) < 40 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close * 1 day ago volume > 1000000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#2** `daily mfi( 14 ) > 80` — Inequality test: left expression must be strictly greater than right.
- **#3** `daily mfi( 21 ) > 80` — Inequality test: left expression must be strictly greater than right.
- **#4** `daily mfi( 28 ) > 80` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily mfi( 35 ) > 80` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily mfi( 42 ) > 80` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **5** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #7
- **Condition (verbatim):** `daily mfi( 14 ) < 40`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `daily mfi( 21 ) < 40`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `daily mfi( 28 ) < 40`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `daily mfi( 35 ) < 40`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `daily mfi( 42 ) < 40`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `mfi` — appears 10 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 6 occurrence(s)
- `<` — 5 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`

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

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **5** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Volume/delivery, Oscillator
- **Tags:** universe:cash, indicator:volume, indicator:mfi, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

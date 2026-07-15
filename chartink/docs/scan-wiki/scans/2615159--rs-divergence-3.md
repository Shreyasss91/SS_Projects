---
scan_id: 2615159
scan_name: rs divergence 3
source_url: https://chartink.com/screener/rs-divergence-3
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery"]
tags: ["universe:cash","indicator:volume","timeframe:daily","timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 5
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# rs divergence 3

## Source

- Chartink URL: https://chartink.com/screener/rs-divergence-3
- Scan ID: `2615159`
- Slug: `rs-divergence-3`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-07-29T02:38:07.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2615159.json](../source-snapshots/2615159.json)
- Text snapshot: [source-snapshots/2615159.txt](../source-snapshots/2615159.txt)

## What this scan is for

This is a **swing** screen over **cash** with **3** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 1000000000
- weekly count streak( 4, 1 where weekly close < 1 week ago close ) >= 4
- daily count streak( 4, 1 where daily close > 1 day ago close ) >= 4

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: rs divergence 3
Scan id: 2615159
Slug: rs-divergence-3
Source URL: https://chartink.com/screener/rs-divergence-3
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-29T02:38:07.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily count( 10, 1 where daily rsi( 14 ) < 1 day ago rsi( 14 ) ) > 6
2. [Disabled] daily count( 10, 1 where daily close > 1 day ago close ) > 6
3. [Enabled] 1 day ago close * 1 day ago volume > 1000000000
4. [Disabled] ( daily rsi( 14 ) - 7 days ago rsi( 14 ) ) / 7 < -1.73
5. [Disabled] ( daily HLC3 - 7 days ago HLC3 ) / 7 < 1.73
6. [Disabled] daily stc( 10 ,  23 ,  50 ,  0.5 ) < 1 day ago stc( 10 ,  23 ,  50 ,  0.5 ) * 0.51
7. [Enabled] weekly count streak( 4, 1 where weekly close < 1 week ago close ) >= 4
8. [Enabled] daily count streak( 4, 1 where daily close > 1 day ago close ) >= 4

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( 1 day ago close * 1 day ago volume > 1000000000 and weekly countstreak( 4, 1 where weekly close < 1 week ago close ) >= 4 and latest countstreak( 4, 1 where latest close > 1 day ago close ) >= 4 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily count( 10, 1 where daily rsi( 14 ) < 1 day ago rsi( 14 ) ) > 6 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 2 | 2 | Disabled | root | daily count( 10, 1 where daily close > 1 day ago close ) > 6 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 3 | 3 | Enabled | root | 1 day ago close * 1 day ago volume > 1000000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 4 | 4 | Disabled | root | ( daily rsi( 14 ) - 7 days ago rsi( 14 ) ) / 7 < -1.73 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 5 | 5 | Disabled | root | ( daily HLC3 - 7 days ago HLC3 ) / 7 < 1.73 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 6 | 6 | Disabled | root | daily stc( 10 ,  23 ,  50 ,  0.5 ) < 1 day ago stc( 10 ,  23 ,  50 ,  0.5 ) * 0.51 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 7 | 7 | Enabled | root | weekly count streak( 4, 1 where weekly close < 1 week ago close ) >= 4 | Inequality test: left expression must be strictly less than right. References weekly bars / weekly offset. |
| 8 | 8 | Enabled | root | daily count streak( 4, 1 where daily close > 1 day ago close ) >= 4 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `1 day ago close * 1 day ago volume > 1000000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#7** `weekly count streak( 4, 1 where weekly close < 1 week ago close ) >= 4` — Inequality test: left expression must be strictly less than right. References weekly bars / weekly offset.
- **#8** `daily count streak( 4, 1 where daily close > 1 day ago close ) >= 4` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **5** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily count( 10, 1 where daily rsi( 14 ) < 1 day ago rsi( 14 ) ) > 6`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `daily count( 10, 1 where daily close > 1 day ago close ) > 6`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `( daily rsi( 14 ) - 7 days ago rsi( 14 ) ) / 7 < -1.73`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `( daily HLC3 - 7 days ago HLC3 ) / 7 < 1.73`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `daily stc( 10 ,  23 ,  50 ,  0.5 ) < 1 day ago stc( 10 ,  23 ,  50 ,  0.5 ) * 0.51`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 7 time(s) in the expression tree
- `rsi` — appears 4 time(s) in the expression tree
- `count` — appears 2 time(s) in the expression tree
- `custom_indicator_4583` — appears 2 time(s) in the expression tree
- `stc` — appears 2 time(s) in the expression tree
- `count streak` — appears 2 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 5 occurrence(s)
- `<` — 5 occurrence(s)
- `*` — 2 occurrence(s)
- `/` — 2 occurrence(s)
- `>=` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `1_days_ago`, `1_weeks_ago`, `7_days_ago`

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

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
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
- **Methods:** Volume/delivery
- **Tags:** universe:cash, indicator:volume, timeframe:daily, timeframe:weekly
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

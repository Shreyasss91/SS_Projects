---
scan_id: 6334594
scan_name: divergence
source_url: https://chartink.com/screener/divergence-339
market: Indian equities
horizon: "Swing"
classification: ["Oscillator"]
tags: ["universe:nifty-200","indicator:rsi","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Oscillator
---

# divergence

## Source

- Chartink URL: https://chartink.com/screener/divergence-339
- Scan ID: `6334594`
- Slug: `divergence-339`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2021-09-28T18:29:32.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/6334594.json](../source-snapshots/6334594.json)
- Text snapshot: [source-snapshots/6334594.txt](../source-snapshots/6334594.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **2** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Oscillator**.

The active tests, in captured order:
- daily close < 30 days ago close * 0.95
- daily rsi( 14 ) > 30 days ago rsi( 14 ) * 1.05

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: divergence
Scan id: 6334594
Slug: divergence-339
Source URL: https://chartink.com/screener/divergence-339
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-09-28T18:29:32.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily close < 30 days ago close * 0.95
2. [Enabled] daily rsi( 14 ) > 30 days ago rsi( 14 ) * 1.05

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( latest close < 30 days ago close * 0.95 and latest rsi( 14 ) > 30 days ago rsi( 14 ) * 1.05 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily close < 30 days ago close * 0.95 | Inequality test: left expression must be strictly less than right. |
| 2 | 2 | Enabled | root | daily rsi( 14 ) > 30 days ago rsi( 14 ) * 1.05 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily close < 30 days ago close * 0.95` — Inequality test: left expression must be strictly less than right.
- **#2** `daily rsi( 14 ) > 30 days ago rsi( 14 ) * 1.05` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.

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
- `close` — appears 2 time(s) in the expression tree
- `rsi` — appears 2 time(s) in the expression tree

### Operators observed
- `*` — 2 occurrence(s)
- `<` — 1 occurrence(s)
- `>` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `30_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Mean reversion.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Stretch conditions can highlight exhaustion zones inside ranges when broader trend is not strongly opposed.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Mean-reversion style thresholds can **fight strong trends** and produce repeated losers in momentum markets.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Oscillator
- **Tags:** universe:nifty-200, indicator:rsi, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

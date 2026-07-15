---
scan_id: 6295708
scan_name: my rsi test
source_url: https://chartink.com/screener/my-rsi-test-1
market: Indian equities
horizon: "Intraday"
classification: ["Other"]
tags: ["universe:futures","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Other
---

# my rsi test

## Source

- Chartink URL: https://chartink.com/screener/my-rsi-test-1
- Scan ID: `6295708`
- Slug: `my-rsi-test-1`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-09-25T17:06:43.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/6295708.json](../source-snapshots/6295708.json)
- Text snapshot: [source-snapshots/6295708.txt](../source-snapshots/6295708.txt)

## What this scan is for

This is a **intraday** screen over **futures** with **1** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Other**.

The active tests, in captured order:
- daily count( 233, 1 where [0] 60 minute close > [-1] 60 minute max( 5 ,  [0] 60 minute close ) ) > daily count( 233, 1 where [0] 60 minute close < [-1] 60 minute min( 5 ,  [0] 60 minute close ) )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: my rsi test
Scan id: 6295708
Slug: my-rsi-test-1
Source URL: https://chartink.com/screener/my-rsi-test-1
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-09-25T17:06:43.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily count( 233, 1 where [0] 60 minute close > [-1] 60 minute max( 5 ,  [0] 60 minute close ) ) > daily count( 233, 1 where [0] 60 minute close < [-1] 60 minute min( 5 ,  [0] 60 minute close ) )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( latest count( 233, 1 where [0] 1 hour close > [-1] 1 hour max( 5 , [0] 1 hour close ) ) > latest count( 233, 1 where [0] 1 hour close < [-1] 1 hour min( 5 , [0] 1 hour close ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily count( 233, 1 where [0] 60 minute close > [-1] 60 minute max( 5 ,  [0] 60 minute close ) ) > daily count( 233, 1 where [0] 60 minute close < [-1] 60 minute min( 5 ,  [0] 60 minute close ) ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily count( 233, 1 where [0] 60 minute close > [-1] 60 minute max( 5 ,  [0] 60 minute close ) ) > daily count( 233, 1 where [0] 60 minute close < [-1] 60 minute min( 5 ,  [0] 60 minute close ) )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `close` — appears 4 time(s) in the expression tree
- `count` — appears 2 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 2 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Other
- **Tags:** universe:futures, timeframe:daily, timeframe:intraday-bars
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

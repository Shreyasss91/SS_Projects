---
scan_id: 24439670
scan_name: MACD constraction
source_url: https://chartink.com/screener/macd-constraction
market: Indian equities
horizon: "Intraday"
classification: ["Oscillator","Momentum"]
tags: ["universe:nifty-200","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Oscillator
---

# MACD constraction

## Source

- Chartink URL: https://chartink.com/screener/macd-constraction
- Scan ID: `24439670`
- Slug: `macd-constraction`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2025-11-10T12:16:03.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24439670.json](../source-snapshots/24439670.json)
- Text snapshot: [source-snapshots/24439670.txt](../source-snapshots/24439670.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **4** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Oscillator, Momentum**.

The active tests, in captured order:
- [-10] 15 minute count( 300, 1 where [0] 15 minute macd line( 12 ,  200 ,  9 ) > 0 ) = 300
- [0] 15 minute macd line( 12 ,  200 ,  9 ) crossed below 0
- daily abs( daily macd histogram( 12 ,  26 ,  9 ) - daily min( 50 ,  daily macd histogram( 12 ,  26 ,  9 ) ) ) / daily macd histogram( 12 ,  26 ,  9 ) < 0.001
- daily abs( daily macd histogram( 12 ,  26 ,  9 ) - daily max( 50 ,  daily macd histogram( 12 ,  26 ,  9 ) ) ) / daily macd histogram( 12 ,  26 ,  9 ) < 0.001

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: MACD constraction
Scan id: 24439670
Slug: macd-constraction
Source URL: https://chartink.com/screener/macd-constraction
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-10T12:16:03.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily stddva( close ,  20 ) crossed below 1
2. [Disabled] [0] 15 minute stddva( close ,  40 ) crossed below 0.2
3. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
4. [Enabled] [-10] 15 minute count( 300, 1 where [0] 15 minute macd line( 12 ,  200 ,  9 ) > 0 ) = 300
    group_path: root/group[cash|all]
5. [Enabled] [0] 15 minute macd line( 12 ,  200 ,  9 ) crossed below 0
    group_path: root/group[cash|all]
6. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Enabled] daily abs( daily macd histogram( 12 ,  26 ,  9 ) - daily min( 50 ,  daily macd histogram( 12 ,  26 ,  9 ) ) ) / daily macd histogram( 12 ,  26 ,  9 ) < 0.001
    group_path: root/group[cash|all]
8. [Enabled] daily abs( daily macd histogram( 12 ,  26 ,  9 ) - daily max( 50 ,  daily macd histogram( 12 ,  26 ,  9 ) ) ) / daily macd histogram( 12 ,  26 ,  9 ) < 0.001
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( abs( daily macd histogram( 12 , 26 , 9 ) - daily min( 50 , daily macd histogram( 12 , 26 , 9 ) ) ) / daily macd histogram( 12 , 26 , 9 ) < 0.001 and abs( daily macd histogram( 12 , 26 , 9 ) - daily max( 50 , daily macd histogram( 12 , 26 , 9 ) ) ) / daily macd histogram( 12 , 26 , 9 ) < 0.001 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily stddva( close ,  20 ) crossed below 1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 2 | 2 | Disabled | root | [0] 15 minute stddva( close ,  40 ) crossed below 0.2 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 4 | Enabled | root/group[cash\|all] | [-10] 15 minute count( 300, 1 where [0] 15 minute macd line( 12 ,  200 ,  9 ) > 0 ) = 300 | Inequality test: left expression must be strictly greater than right. MACD uses EMA differences (line/signal/histogram depending on field). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 5 | Enabled | root/group[cash\|all] | [0] 15 minute macd line( 12 ,  200 ,  9 ) crossed below 0 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). MACD uses EMA differences (line/signal/histogram depending on field). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 7 | Enabled | root/group[cash\|all] | daily abs( daily macd histogram( 12 ,  26 ,  9 ) - daily min( 50 ,  daily macd histogram( 12 ,  26 ,  9 ) ) ) / daily macd histogram( 12 ,  26 ,  9 ) < 0.001 | Inequality test: left expression must be strictly less than right. MACD uses EMA differences (line/signal/histogram depending on field). min(N, series) is the lowest value of series over N bars. |
| 6 | 8 | Enabled | root/group[cash\|all] | daily abs( daily macd histogram( 12 ,  26 ,  9 ) - daily max( 50 ,  daily macd histogram( 12 ,  26 ,  9 ) ) ) / daily macd histogram( 12 ,  26 ,  9 ) < 0.001 | Inequality test: left expression must be strictly less than right. MACD uses EMA differences (line/signal/histogram depending on field). max(N, series) is the highest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#4** `[-10] 15 minute count( 300, 1 where [0] 15 minute macd line( 12 ,  200 ,  9 ) > 0 ) = 300` — Inequality test: left expression must be strictly greater than right. MACD uses EMA differences (line/signal/histogram depending on field). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[0] 15 minute macd line( 12 ,  200 ,  9 ) crossed below 0` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). MACD uses EMA differences (line/signal/histogram depending on field). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `daily abs( daily macd histogram( 12 ,  26 ,  9 ) - daily min( 50 ,  daily macd histogram( 12 ,  26 ,  9 ) ) ) / daily macd histogram( 12 ,  26 ,  9 ) < 0.001` — Inequality test: left expression must be strictly less than right. MACD uses EMA differences (line/signal/histogram depending on field). min(N, series) is the lowest value of series over N bars.
- **#8** `daily abs( daily macd histogram( 12 ,  26 ,  9 ) - daily max( 50 ,  daily macd histogram( 12 ,  26 ,  9 ) ) ) / daily macd histogram( 12 ,  26 ,  9 ) < 0.001` — Inequality test: left expression must be strictly less than right. MACD uses EMA differences (line/signal/histogram depending on field). max(N, series) is the highest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily stddva( close ,  20 ) crossed below 1`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `[0] 15 minute stddva( close ,  40 ) crossed below 0.2`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `macd histogram` — appears 8 time(s) in the expression tree
- `macd line` — appears 5 time(s) in the expression tree
- `stddva` — appears 2 time(s) in the expression tree
- `abs` — appears 2 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed below` — 3 occurrence(s)
- `/` — 2 occurrence(s)
- `<` — 2 occurrence(s)
- `=` — 1 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `15_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Volatility, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Oscillator, Momentum
- **Tags:** universe:nifty-200, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

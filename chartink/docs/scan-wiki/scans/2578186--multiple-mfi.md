---
scan_id: 2578186
scan_name: Multiple MFI
source_url: https://chartink.com/screener/multiple-mfi
market: Indian equities
horizon: Intraday
classification: ["Oscillator", "Moving average", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:futures", "indicator:vwap", "indicator:mfi", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 7
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Oscillator
---

# Multiple MFI

## Source

- Chartink URL: https://chartink.com/screener/multiple-mfi
- Scan ID: `2578186`
- Slug: `multiple-mfi`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2020-07-24T09:22:01.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2578186.json](../source-snapshots/2578186.json)
- Text snapshot: [source-snapshots/2578186.txt](../source-snapshots/2578186.txt)

## What this scan is for

This scan, titled "Multiple MFI", appears designed to screen Indian equities in the **futures** universe using **2 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Oscillator, Moving average, Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 240_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Multiple MFI
Scan id: 2578186
Slug: multiple-mfi
Source URL: https://chartink.com/screener/multiple-mfi
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-24T09:22:01.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] daily close crossed above daily hma( close ,  200 )
2. [Disabled] daily close crossed above daily hma( close ,  220 )
3. [Disabled] daily close crossed above daily hma( close ,  240 )
4. [Disabled] ( daily hma( close ,  200 ) + daily hma( close ,  300 ) + daily hma( close ,  400 ) ) / 3 crossed above daily close
5. [Disabled] daily abs( [0] 240 minute hma( close ,  20 ) - [0] 240 minute hma( close ,  30 ) ) < [0] 240 minute close * 0.005
6. [Enabled] daily abs( daily close - daily hma( close ,  200 ) ) < daily close * 0.002
7. [Enabled] daily abs( daily close - daily vwap ) < daily close * 0.002
8. [Disabled] daily abs( [0] 240 minute hma( close ,  30 ) - [0] 240 minute hma( close ,  40 ) ) < [0] 240 minute close * 0.005
9. [Disabled] daily abs( [0] 240 minute hma( close ,  20 ) - [0] 240 minute hma( close ,  40 ) ) < [0] 240 minute close * 0.005

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( abs( latest close - latest "wma( ( ( 2 * wma( (latest close), 100) ) - wma((latest close), 200) ), 14)" ) < latest close * 0.002 and abs( latest close - latest vwap ) < latest close * 0.002 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | daily close crossed above daily hma( close ,  200 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 2 | Disabled | daily close crossed above daily hma( close ,  220 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 3 | Disabled | daily close crossed above daily hma( close ,  240 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 4 | Disabled | ( daily hma( close ,  200 ) + daily hma( close ,  300 ) + daily hma( close ,  400 ) ) / 3 crossed above daily close | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 5 | Disabled | daily abs( [0] 240 minute hma( close ,  20 ) - [0] 240 minute hma( close ,  30 ) ) < [0] 240 minute close * 0.005 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | Enabled | daily abs( daily close - daily hma( close ,  200 ) ) < daily close * 0.002 | Inequality test: left expression must be strictly less than right. |
| 7 | Enabled | daily abs( daily close - daily vwap ) < daily close * 0.002 | Inequality test: left expression must be strictly less than right. VWAP is volume-weighted average price for the session/period context Chartink supplies. |
| 8 | Disabled | daily abs( [0] 240 minute hma( close ,  30 ) - [0] 240 minute hma( close ,  40 ) ) < [0] 240 minute close * 0.005 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | Disabled | daily abs( [0] 240 minute hma( close ,  20 ) - [0] 240 minute hma( close ,  40 ) ) < [0] 240 minute close * 0.005 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#6** `daily abs( daily close - daily hma( close ,  200 ) ) < daily close * 0.002` — Inequality test: left expression must be strictly less than right.
- **#7** `daily abs( daily close - daily vwap ) < daily close * 0.002` — Inequality test: left expression must be strictly less than right. VWAP is volume-weighted average price for the session/period context Chartink supplies.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **7** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily close crossed above daily hma( close ,  200 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `daily close crossed above daily hma( close ,  220 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `daily close crossed above daily hma( close ,  240 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `( daily hma( close ,  200 ) + daily hma( close ,  300 ) + daily hma( close ,  400 ) ) / 3 crossed above daily close`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily abs( [0] 240 minute hma( close ,  20 ) - [0] 240 minute hma( close ,  30 ) ) < [0] 240 minute close * 0.005`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `daily abs( [0] 240 minute hma( close ,  30 ) - [0] 240 minute hma( close ,  40 ) ) < [0] 240 minute close * 0.005`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `daily abs( [0] 240 minute hma( close ,  20 ) - [0] 240 minute hma( close ,  40 ) ) < [0] 240 minute close * 0.005`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 24 time(s) in the expression tree
- `hma` — appears 13 time(s) in the expression tree
- `abs` — appears 5 time(s) in the expression tree
- `vwap` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 5 occurrence(s)
- `*` — 5 occurrence(s)
- `crossed above` — 4 occurrence(s)
- `/` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `240_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **7** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Oscillator, Moving average, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:futures, indicator:vwap, indicator:mfi, timeframe:intraday-bars, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

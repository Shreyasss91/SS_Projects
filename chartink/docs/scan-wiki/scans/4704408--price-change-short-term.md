---
scan_id: 4704408
scan_name: Price Change Short term
source_url: https://chartink.com/screener/price-change-33
market: Indian equities
horizon: Multi-horizon
classification: ["Momentum", "Price action"]
tags: ["short-bias", "universe:sbin", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 1
needs_review_filter_count: 0
root_segment: SBIN
root_join: any
primary_classification: Momentum
---

# Price Change Short term

## Source

- Chartink URL: https://chartink.com/screener/price-change-33
- Scan ID: `4704408`
- Slug: `price-change-33`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2021-05-27T19:12:36.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4704408.json](../source-snapshots/4704408.json)
- Text snapshot: [source-snapshots/4704408.txt](../source-snapshots/4704408.txt)

## What this scan is for

This scan, titled "Price Change Short term", appears designed to screen Indian equities in the **SBIN** universe using **2 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Momentum, Price action**. Likely horizon label from name/timeframes: **Multi-horizon**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 15_minute, 1_minute`.

Author description (source metadata): Signals are Dips, Buy stock for short term or intraday

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Price Change Short term
Scan id: 4704408
Slug: price-change-33
Source URL: https://chartink.com/screener/price-change-33
Root universe/segment: SBIN
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-05-27T19:12:36.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [0] 15 minute sum( close ,  300 ) crossed below -11
2. [Enabled] [0] 1 minute sum( close ,  300 ) crossed below -1
3. [Enabled] [0] 15 minute sum( close ,  20 ) crossed below -5

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( sbin ( [0] 1 minute sum( [0] 1 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) < -1 and [ -1 ] 1 minute sum( [0] 1 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) >= -1 or [0] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 20 ) < -5 and [ -1 ] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 20 ) >= -5 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [0] 15 minute sum( close ,  300 ) crossed below -11 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | Enabled | [0] 1 minute sum( close ,  300 ) crossed below -1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | Enabled | [0] 15 minute sum( close ,  20 ) crossed below -5 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[0] 1 minute sum( close ,  300 ) crossed below -1` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#3** `[0] 15 minute sum( close ,  20 ) crossed below -5` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **1** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `[0] 15 minute sum( close ,  300 ) crossed below -11`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `sum` — appears 3 time(s) in the expression tree
- `close` — appears 3 time(s) in the expression tree
- `% change` — appears 2 time(s) in the expression tree

### Operators observed
- `crossed below` — 3 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **SBIN**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **SBIN**. Liquidity and index membership still vary inside that set.
- **Method context:** Momentum, Price action.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **SBIN**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **1** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Momentum, Price action
- **Tags:** short-bias, universe:sbin, timeframe:intraday-bars, timeframe:daily
- **Root universe:** SBIN
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

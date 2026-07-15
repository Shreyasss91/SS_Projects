---
scan_id: 14468705
scan_name: square root black wolf money
source_url: https://chartink.com/screener/square-root-black-wolf-money
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:nifty-200", "indicator:volume", "indicator:ema", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 1
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# square root black wolf money

## Source

- Chartink URL: https://chartink.com/screener/square-root-black-wolf-money
- Scan ID: `14468705`
- Slug: `square-root-black-wolf-money`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2024-01-03T02:46:12.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14468705.json](../source-snapshots/14468705.json)
- Text snapshot: [source-snapshots/14468705.txt](../source-snapshots/14468705.txt)

## What this scan is for

This scan, titled "square root black wolf money", appears designed to screen Indian equities in the **nifty 200** universe using **1 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Moving average, Volume/delivery, Momentum, Multi-factor**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 15_minute, 5_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: square root black wolf money
Scan id: 14468705
Slug: square-root-black-wolf-money
Source URL: https://chartink.com/screener/square-root-black-wolf-money
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2024-01-03T02:46:12.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] daily square root( daily abs( [0] 5 minute ema( close ,  30 ) - [0] 5 minute ema( close ,  30 ) ) ) crossed above 400
2. [Enabled] daily square root( daily abs( [0] 15 minute ema( close ,  30 ) - [0] 15 minute ema( close ,  30 ) ) ) crossed above 800

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( square root( abs( [0] 15 minute ema( greatest(  ( [0] 15 minute close - [-1] 15 minute close ) * [0] 15 minute volume, 0  ) , 30 ) - [0] 15 minute ema( greatest(  ( [-1] 15 minute close - [0] 15 minute close ) * [0] 15 minute volume, 0  ) , 30 ) ) ) > 800 and square root( abs( [ -1 ] 15 minute ema( greatest(  ( [0] 15 minute close - [-1] 15 minute close ) * [0] 15 minute volume, 0  ) , 30 )- [ -1 ] 15 minute ema( greatest(  ( [-1] 15 minute close - [0] 15 minute close ) * [0] 15 minute volume, 0  ) , 30 )) ) <= 800 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | daily square root( daily abs( [0] 5 minute ema( close ,  30 ) - [0] 5 minute ema( close ,  30 ) ) ) crossed above 400 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | Enabled | daily square root( daily abs( [0] 15 minute ema( close ,  30 ) - [0] 15 minute ema( close ,  30 ) ) ) crossed above 800 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). EMA is an exponentially weighted moving average of the chosen field. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily square root( daily abs( [0] 15 minute ema( close ,  30 ) - [0] 15 minute ema( close ,  30 ) ) ) crossed above 800` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). EMA is an exponentially weighted moving average of the chosen field. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **1** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily square root( daily abs( [0] 5 minute ema( close ,  30 ) - [0] 5 minute ema( close ,  30 ) ) ) crossed above 400`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 8 time(s) in the expression tree
- `ema` — appears 4 time(s) in the expression tree
- `greatest` — appears 4 time(s) in the expression tree
- `volume` — appears 4 time(s) in the expression tree
- `square root` — appears 2 time(s) in the expression tree
- `abs` — appears 2 time(s) in the expression tree

### Operators observed
- `*` — 4 occurrence(s)
- `crossed above` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `15_minute`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **1** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Moving average, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:nifty-200, indicator:volume, indicator:ema, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

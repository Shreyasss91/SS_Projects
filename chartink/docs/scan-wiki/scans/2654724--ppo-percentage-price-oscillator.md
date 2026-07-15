---
scan_id: 2654724
scan_name: PPO PERCENTAGE PRICE OSCILLATOR
source_url: https://chartink.com/screener/ppo-percentage-price-oscillator
market: Indian equities
horizon: "Swing"
classification: ["Momentum"]
tags: ["universe:cash","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 9
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Momentum
---

# PPO PERCENTAGE PRICE OSCILLATOR

## Source

- Chartink URL: https://chartink.com/screener/ppo-percentage-price-oscillator
- Scan ID: `2654724`
- Slug: `ppo-percentage-price-oscillator`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-08-03T09:31:26.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2654724.json](../source-snapshots/2654724.json)
- Text snapshot: [source-snapshots/2654724.txt](../source-snapshots/2654724.txt)

## What this scan is for

This is a **swing** screen over **cash** with **2** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Momentum**.

The active tests, in captured order:
- 1 day ago close*vol > 100000000
- daily custom_indicator_4810 crossed above 10

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: PPO PERCENTAGE PRICE OSCILLATOR
Scan id: 2654724
Slug: ppo-percentage-price-oscillator
Source URL: https://chartink.com/screener/ppo-percentage-price-oscillator
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-08-03T09:31:26.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close*vol > 100000000
2. [Enabled] daily custom_indicator_4810 crossed above 10
3. [Disabled] daily custom_indicator_4810 crossed below -3
4. [Disabled] daily custom_indicator_4810 crossed above 0
5. [Disabled] daily custom_indicator_4810 crossed below daily ema( close ,  9 )
6. [Disabled] daily max( 14 ,  daily high ) > 14 days ago max( 14 ,  daily high )
7. [Disabled] daily max( 14 ,  daily custom_indicator_4810 ) < 14 days ago max( 14 ,  daily custom_indicator_4810 )
8. [Disabled] 14 days ago max( 14 ,  14 days ago high ) > 28 days ago max( 14 ,  daily high )
9. [Disabled] 14 days ago max( 14 ,  daily custom_indicator_4810 ) < 28 days ago max( 14 ,  daily custom_indicator_4810 )
10. [Disabled] 28 days ago max( 14 ,  daily high ) > 42 days ago max( 14 ,  daily high )
11. [Disabled] 28 days ago max( 14 ,  daily custom_indicator_4810 ) < 42 days ago max( 14 ,  daily custom_indicator_4810 )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( 1 day ago "close *  volume" > 100000000 and latest  "( (  ema(  close , 12 ) -  ema(  close , 26 ) ) /  ema(  close , 26 ) ) * 100" > 10 and 1 day ago   "( (  ema(  close , 12 ) -  ema(  close , 26 ) ) /  ema(  close , 26 ) ) * 100" <= 10 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 1 day ago close*vol > 100000000 | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | daily custom_indicator_4810 crossed above 10 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). |
| 3 | 3 | Disabled | root | daily custom_indicator_4810 crossed below -3 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 4 | 4 | Disabled | root | daily custom_indicator_4810 crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 5 | 5 | Disabled | root | daily custom_indicator_4810 crossed below daily ema( close ,  9 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. |
| 6 | 6 | Disabled | root | daily max( 14 ,  daily high ) > 14 days ago max( 14 ,  daily high ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 7 | 7 | Disabled | root | daily max( 14 ,  daily custom_indicator_4810 ) < 14 days ago max( 14 ,  daily custom_indicator_4810 ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 8 | 8 | Disabled | root | 14 days ago max( 14 ,  14 days ago high ) > 28 days ago max( 14 ,  daily high ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 9 | 9 | Disabled | root | 14 days ago max( 14 ,  daily custom_indicator_4810 ) < 28 days ago max( 14 ,  daily custom_indicator_4810 ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 10 | 10 | Disabled | root | 28 days ago max( 14 ,  daily high ) > 42 days ago max( 14 ,  daily high ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 11 | 11 | Disabled | root | 28 days ago max( 14 ,  daily custom_indicator_4810 ) < 42 days ago max( 14 ,  daily custom_indicator_4810 ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close*vol > 100000000` — Inequality test: left expression must be strictly greater than right.
- **#2** `daily custom_indicator_4810 crossed above 10` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar).

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **9** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily custom_indicator_4810 crossed below -3`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `daily custom_indicator_4810 crossed above 0`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily custom_indicator_4810 crossed below daily ema( close ,  9 )`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `daily max( 14 ,  daily high ) > 14 days ago max( 14 ,  daily high )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `daily max( 14 ,  daily custom_indicator_4810 ) < 14 days ago max( 14 ,  daily custom_indicator_4810 )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `14 days ago max( 14 ,  14 days ago high ) > 28 days ago max( 14 ,  daily high )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `14 days ago max( 14 ,  daily custom_indicator_4810 ) < 28 days ago max( 14 ,  daily custom_indicator_4810 )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `28 days ago max( 14 ,  daily high ) > 42 days ago max( 14 ,  daily high )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `28 days ago max( 14 ,  daily custom_indicator_4810 ) < 42 days ago max( 14 ,  daily custom_indicator_4810 )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `max` — appears 12 time(s) in the expression tree
- `custom_indicator_4810` — appears 11 time(s) in the expression tree
- `high` — appears 6 time(s) in the expression tree
- `custom_indicator_4684` — appears 1 time(s) in the expression tree
- `ema` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 4 occurrence(s)
- `<` — 3 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `crossed below` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `14_days_ago`, `1_days_ago`, `28_days_ago`, `42_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **9** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Momentum
- **Tags:** universe:cash, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

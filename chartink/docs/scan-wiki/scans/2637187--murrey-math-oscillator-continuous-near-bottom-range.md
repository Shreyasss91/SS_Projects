---
scan_id: 2637187
scan_name: Murrey Math Oscillator continuous near bottom range
source_url: https://chartink.com/screener/murrey-math-oscillator-pullback
market: Indian equities
horizon: Swing
classification: ["Volatility"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-50", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Volatility
---

# Murrey Math Oscillator continuous near bottom range

## Source

- Chartink URL: https://chartink.com/screener/murrey-math-oscillator-pullback
- Scan ID: `2637187`
- Slug: `murrey-math-oscillator-pullback`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-08-01T04:23:42.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2637187.json](../source-snapshots/2637187.json)
- Text snapshot: [source-snapshots/2637187.txt](../source-snapshots/2637187.txt)

## What this scan is for

This is a **swing** screen over **nifty 500** with **6** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Volatility**.
The active tests, in captured order, are:
- 1 day ago close*vol > 1000000000
- ( daily close - daily min( 100 ,  daily low ) + ( ( ( daily max( 100 ,  daily high ) - daily min( 100 ,  daily low ) ) * 0.125 ) * 4 ) ) / ( ( daily max( 100 ,  daily high ) - daily min( 100 ,  daily low ) ) / 2 ) < 1.2
- ( 1 day ago close - 1 day ago min( 100 ,  1 day ago low ) + ( ( ( 1 day ago max( 100 ,  1 day ago high ) - 1 day ago min( 100 ,  1 day ago low ) ) * 0.125 ) * 4 ) ) / ( ( 1 day ago max( 100 ,  1 day ago high ) - 1 day ago min( 100 ,  1 day ago low ) ) / 2 ) < 1.2
- ( 2 days ago close - 2 days ago min( 100 ,  2 days ago low ) + ( ( ( 2 days ago max( 100 ,  2 days ago high ) - 2 days ago min( 100 ,  2 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 2 days ago max( 100 ,  2 days ago high ) - 2 days ago min( 100 ,  2 days ago low ) ) / 2 ) < 1.2
- ( 3 days ago close - 3 days ago min( 100 ,  4 days ago low ) + ( ( ( 4 days ago max( 100 ,  4 days ago high ) - 4 days ago min( 100 ,  4 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 4 days ago max( 100 ,  4 days ago high ) - 4 days ago min( 100 ,  4 days ago low ) ) / 2 ) < 1.2
- ( 4 days ago close - 4 days ago min( 100 ,  3 days ago low ) + ( ( ( 3 days ago max( 100 ,  3 days ago high ) - 3 days ago min( 100 ,  3 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 3 days ago max( 100 ,  3 days ago high ) - 3 days ago min( 100 ,  3 days ago low ) ) / 2 ) < 1.2

Author description (source metadata): UCS_Murrey's Math Oscillator_V2
(close-min(len,low)+(((max(len,high)-min(len,low))*mult)*4))/((max(len,high)-min(len,low))/2) > 2.75
Has 3 parameters
1. LOOKBACKPERIOD -- Parameter in max and  min function
2. multiplication factor -- (default:0.125) parameter multiplied to difference between max and min functions
3. timeframe
4. varies from 1 to 3  
    greater than > 2.75 overbought?
    less than < 1.25 oversold?

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Murrey Math Oscillator continuous near bottom range
Scan id: 2637187
Slug: murrey-math-oscillator-pullback
Source URL: https://chartink.com/screener/murrey-math-oscillator-pullback
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-08-01T04:23:42.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close*vol > 1000000000
2. [Disabled] 1 day ago close*vol < 1000000000
3. [Disabled] 1 day ago close*vol > 100000000
4. [Enabled] ( daily close - daily min( 100 ,  daily low ) + ( ( ( daily max( 100 ,  daily high ) - daily min( 100 ,  daily low ) ) * 0.125 ) * 4 ) ) / ( ( daily max( 100 ,  daily high ) - daily min( 100 ,  daily low ) ) / 2 ) < 1.2
5. [Enabled] ( 1 day ago close - 1 day ago min( 100 ,  1 day ago low ) + ( ( ( 1 day ago max( 100 ,  1 day ago high ) - 1 day ago min( 100 ,  1 day ago low ) ) * 0.125 ) * 4 ) ) / ( ( 1 day ago max( 100 ,  1 day ago high ) - 1 day ago min( 100 ,  1 day ago low ) ) / 2 ) < 1.2
6. [Enabled] ( 2 days ago close - 2 days ago min( 100 ,  2 days ago low ) + ( ( ( 2 days ago max( 100 ,  2 days ago high ) - 2 days ago min( 100 ,  2 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 2 days ago max( 100 ,  2 days ago high ) - 2 days ago min( 100 ,  2 days ago low ) ) / 2 ) < 1.2
7. [Enabled] ( 3 days ago close - 3 days ago min( 100 ,  4 days ago low ) + ( ( ( 4 days ago max( 100 ,  4 days ago high ) - 4 days ago min( 100 ,  4 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 4 days ago max( 100 ,  4 days ago high ) - 4 days ago min( 100 ,  4 days ago low ) ) / 2 ) < 1.2
8. [Enabled] ( 4 days ago close - 4 days ago min( 100 ,  3 days ago low ) + ( ( ( 3 days ago max( 100 ,  3 days ago high ) - 3 days ago min( 100 ,  3 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 3 days ago max( 100 ,  3 days ago high ) - 3 days ago min( 100 ,  3 days ago low ) ) / 2 ) < 1.2

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 500 ( 1 day ago "close *  volume" > 1000000000 and( latest close - latest min( 100 , latest low ) + ( ( ( latest max( 100 , latest high ) - latest min( 100 , latest low ) ) * 0.125 ) * 4 ) ) / ( ( latest max( 100 , latest high ) - latest min( 100 , latest low ) ) / 2 ) < 1.2 and( 1 day ago close - 1 day ago min( 100 , 1 day ago low ) + ( ( ( 1 day ago max( 100 , 1 day ago high ) - 1 day ago min( 100 , 1 day ago low ) ) * 0.125 ) * 4 ) ) / ( ( 1 day ago max( 100 , 1 day ago high ) - 1 day ago min( 100 , 1 day ago low ) ) / 2 ) < 1.2 and( 2 days ago close - 2 days ago min( 100 , 2 days ago low ) + ( ( ( 2 days ago max( 100 , 2 days ago high ) - 2 days ago min( 100 , 2 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 2 days ago max( 100 , 2 days ago high ) - 2 days ago min( 100 , 2 days ago low ) ) / 2 ) < 1.2 and( 3 days ago close - 3 days ago min( 100 , 4 days ago low ) + ( ( ( 4 days ago max( 100 , 4 days ago high ) - 4 days ago min( 100 , 4 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 4 days ago max( 100 , 4 days ago high ) - 4 days ago min( 100 , 4 days ago low ) ) / 2 ) < 1.2 and( 4 days ago close - 4 days ago min( 100 , 3 days ago low ) + ( ( ( 3 days ago max( 100 , 3 days ago high ) - 3 days ago min( 100 , 3 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 3 days ago max( 100 , 3 days ago high ) - 3 days ago min( 100 , 3 days ago low ) ) / 2 ) < 1.2 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 1 day ago close*vol > 1000000000 | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Disabled | root | 1 day ago close*vol < 1000000000 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 3 | 3 | Disabled | root | 1 day ago close*vol > 100000000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 4 | 4 | Enabled | root | ( daily close - daily min( 100 ,  daily low ) + ( ( ( daily max( 100 ,  daily high ) - daily min( 100 ,  daily low ) ) * 0.125 ) * 4 ) ) / ( ( daily max( 100 ,  daily high ) - daily min( 100 ,  daily low ) ) / 2 ) < 1.2 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 5 | 5 | Enabled | root | ( 1 day ago close - 1 day ago min( 100 ,  1 day ago low ) + ( ( ( 1 day ago max( 100 ,  1 day ago high ) - 1 day ago min( 100 ,  1 day ago low ) ) * 0.125 ) * 4 ) ) / ( ( 1 day ago max( 100 ,  1 day ago high ) - 1 day ago min( 100 ,  1 day ago low ) ) / 2 ) < 1.2 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 6 | 6 | Enabled | root | ( 2 days ago close - 2 days ago min( 100 ,  2 days ago low ) + ( ( ( 2 days ago max( 100 ,  2 days ago high ) - 2 days ago min( 100 ,  2 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 2 days ago max( 100 ,  2 days ago high ) - 2 days ago min( 100 ,  2 days ago low ) ) / 2 ) < 1.2 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 7 | 7 | Enabled | root | ( 3 days ago close - 3 days ago min( 100 ,  4 days ago low ) + ( ( ( 4 days ago max( 100 ,  4 days ago high ) - 4 days ago min( 100 ,  4 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 4 days ago max( 100 ,  4 days ago high ) - 4 days ago min( 100 ,  4 days ago low ) ) / 2 ) < 1.2 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 8 | 8 | Enabled | root | ( 4 days ago close - 4 days ago min( 100 ,  3 days ago low ) + ( ( ( 3 days ago max( 100 ,  3 days ago high ) - 3 days ago min( 100 ,  3 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 3 days ago max( 100 ,  3 days ago high ) - 3 days ago min( 100 ,  3 days ago low ) ) / 2 ) < 1.2 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close*vol > 1000000000` — Inequality test: left expression must be strictly greater than right.
- **#4** `( daily close - daily min( 100 ,  daily low ) + ( ( ( daily max( 100 ,  daily high ) - daily min( 100 ,  daily low ) ) * 0.125 ) * 4 ) ) / ( ( daily max( 100 ,  daily high ) - daily min( 100 ,  daily low ) ) / 2 ) < 1.2` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#5** `( 1 day ago close - 1 day ago min( 100 ,  1 day ago low ) + ( ( ( 1 day ago max( 100 ,  1 day ago high ) - 1 day ago min( 100 ,  1 day ago low ) ) * 0.125 ) * 4 ) ) / ( ( 1 day ago max( 100 ,  1 day ago high ) - 1 day ago min( 100 ,  1 day ago low ) ) / 2 ) < 1.2` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#6** `( 2 days ago close - 2 days ago min( 100 ,  2 days ago low ) + ( ( ( 2 days ago max( 100 ,  2 days ago high ) - 2 days ago min( 100 ,  2 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 2 days ago max( 100 ,  2 days ago high ) - 2 days ago min( 100 ,  2 days ago low ) ) / 2 ) < 1.2` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#7** `( 3 days ago close - 3 days ago min( 100 ,  4 days ago low ) + ( ( ( 4 days ago max( 100 ,  4 days ago high ) - 4 days ago min( 100 ,  4 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 4 days ago max( 100 ,  4 days ago high ) - 4 days ago min( 100 ,  4 days ago low ) ) / 2 ) < 1.2` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#8** `( 4 days ago close - 4 days ago min( 100 ,  3 days ago low ) + ( ( ( 3 days ago max( 100 ,  3 days ago high ) - 3 days ago min( 100 ,  3 days ago low ) ) * 0.125 ) * 4 ) ) / ( ( 3 days ago max( 100 ,  3 days ago high ) - 3 days ago min( 100 ,  3 days ago low ) ) / 2 ) < 1.2` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #2
- **Condition (verbatim):** `1 day ago close*vol < 1000000000`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `1 day ago close*vol > 100000000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `min` — appears 15 time(s) in the expression tree
- `low` — appears 15 time(s) in the expression tree
- `max` — appears 10 time(s) in the expression tree
- `high` — appears 10 time(s) in the expression tree
- `close` — appears 5 time(s) in the expression tree
- `custom_indicator_4684` — appears 3 time(s) in the expression tree

### Operators observed
- `<` — 6 occurrence(s)
- `/` — 5 occurrence(s)
- `>` — 2 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **nifty 500**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`, `4_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volatility
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-50, timeframe:daily
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

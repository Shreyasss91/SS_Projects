---
scan_id: 11581030
scan_name: sma crossover
source_url: https://chartink.com/screener/sma-crossover-1157
market: Indian equities
horizon: Swing
classification: ["Fundamental", "Moving average", "Trend following", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 7
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Fundamental
---

# sma crossover

## Source

- Chartink URL: https://chartink.com/screener/sma-crossover-1157
- Scan ID: `11581030`
- Slug: `sma-crossover-1157`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-04-26T07:11:30.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11581030.json](../source-snapshots/11581030.json)
- Text snapshot: [source-snapshots/11581030.txt](../source-snapshots/11581030.txt)

## What this scan is for

This is a **swing** screen over **cash** with **7** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Fundamental, Moving average, Trend following, Momentum, Multi-factor**.
The active tests, in captured order, are:
- daily market cap > 1000
- daily close > daily sma( close ,  50 )
- 7 days ago sma( close ,  50 ) < daily least
- daily sma( close ,  50 ) > daily greatest
- daily sma( close ,  50 ) crossed above daily sma( close ,  100 )
- daily sma( close ,  50 ) crossed above daily sma( close ,  150 )
- daily sma( close ,  50 ) crossed above daily sma( close ,  200 )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: sma crossover
Scan id: 11581030
Slug: sma-crossover-1157
Source URL: https://chartink.com/screener/sma-crossover-1157
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-26T07:11:30.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily market cap > 1000
2. [Enabled] daily close > daily sma( close ,  50 )
3. [Disabled] daily sma( close ,  150 ) crossed above daily sma( close ,  200 )
4. [Disabled] daily sma( close ,  100 ) crossed above daily sma( close ,  200 )
5. [Enabled] 7 days ago sma( close ,  50 ) < daily least
6. [Enabled] daily sma( close ,  50 ) > daily greatest
7. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
8. [Enabled] daily sma( close ,  50 ) crossed above daily sma( close ,  100 )
    group_path: root/group[cash|any]
9. [Enabled] daily sma( close ,  50 ) crossed above daily sma( close ,  150 )
    group_path: root/group[cash|any]
10. [Enabled] daily sma( close ,  50 ) crossed above daily sma( close ,  200 )
    group_path: root/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( market cap > 1000 and latest close > latest sma( latest close , 50 ) and 7 days ago sma( latest close , 50 ) < least(  7 days ago sma( latest close , 100 ), 7 days ago sma( latest close , 150 ), 7 days ago sma( latest close , 200 )  ) and latest sma( latest close , 50 ) > greatest(  latest sma( latest close , 100 ), latest sma( latest close , 150 ), latest sma( latest close , 200 )  ) and( cash ( latest sma( latest close , 50 ) > latest sma( latest close , 100 ) and 1 day ago  sma( latest close , 50 )<= 1 day ago  sma( latest close , 100 ) or latest sma( latest close , 50 ) > latest sma( latest close , 150 ) and 1 day ago  sma( latest close , 50 )<= 1 day ago  sma( latest close , 150 ) or latest sma( latest close , 50 ) > latest sma( latest close , 200 ) and 1 day ago  sma( latest close , 50 )<= 1 day ago  sma( latest close , 200 ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily market cap > 1000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 2 | 2 | Enabled | root | daily close > daily sma( close ,  50 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 3 | 3 | Disabled | root | daily sma( close ,  150 ) crossed above daily sma( close ,  200 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. |
| 4 | 4 | Disabled | root | daily sma( close ,  100 ) crossed above daily sma( close ,  200 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. |
| 5 | 5 | Enabled | root | 7 days ago sma( close ,  50 ) < daily least | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 6 | 6 | Enabled | root | daily sma( close ,  50 ) > daily greatest | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 7 | 8 | Enabled | root/group[cash\|any] | daily sma( close ,  50 ) crossed above daily sma( close ,  100 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 8 | 9 | Enabled | root/group[cash\|any] | daily sma( close ,  50 ) crossed above daily sma( close ,  150 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 9 | 10 | Enabled | root/group[cash\|any] | daily sma( close ,  50 ) crossed above daily sma( close ,  200 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **7** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily market cap > 1000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#2** `daily close > daily sma( close ,  50 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#5** `7 days ago sma( close ,  50 ) < daily least` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#6** `daily sma( close ,  50 ) > daily greatest` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#8** `daily sma( close ,  50 ) crossed above daily sma( close ,  100 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#9** `daily sma( close ,  50 ) crossed above daily sma( close ,  150 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#10** `daily sma( close ,  50 ) crossed above daily sma( close ,  200 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily sma( close ,  150 ) crossed above daily sma( close ,  200 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `daily sma( close ,  100 ) crossed above daily sma( close ,  200 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 20 time(s) in the expression tree
- `sma` — appears 19 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree
- `least` — appears 1 time(s) in the expression tree
- `greatest` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 5 occurrence(s)
- `>` — 3 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `7_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Moving average, Trend following, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **7** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Fundamental, Moving average, Trend following, Momentum, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, indicator:sma, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

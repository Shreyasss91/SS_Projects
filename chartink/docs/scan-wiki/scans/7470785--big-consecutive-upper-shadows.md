---
scan_id: 7470785
scan_name: Big Consecutive Upper Shadows
source_url: https://chartink.com/screener/big-consecutive-upper-shadows
market: Indian equities
horizon: Swing
classification: ["Fundamental", "Momentum"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "timeframe:daily", "timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 3
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Fundamental
---

# Big Consecutive Upper Shadows

## Source

- Chartink URL: https://chartink.com/screener/big-consecutive-upper-shadows
- Scan ID: `7470785`
- Slug: `big-consecutive-upper-shadows`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2022-01-12T04:11:02.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/7470785.json](../source-snapshots/7470785.json)
- Text snapshot: [source-snapshots/7470785.txt](../source-snapshots/7470785.txt)

## What this scan is for

This is a **swing** screen over **cash** with **3** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Fundamental, Momentum**.
The active tests, in captured order, are:
- daily market cap > 1000
- daily market cap < 10000
- daily count( 21, 1 where daily high > daily greatest * 1.05 ) crossed above 2

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Big Consecutive Upper Shadows
Scan id: 7470785
Slug: big-consecutive-upper-shadows
Source URL: https://chartink.com/screener/big-consecutive-upper-shadows
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-01-12T04:11:02.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily market cap > 1000
    group_path: root/group[cash|all]
3. [Enabled] daily market cap < 10000
    group_path: root/group[cash|all]
4. [Disabled] daily count( 50, 1 where daily volume > 1 day ago sma( close ,  5 ) * 3 ) crossed above 5
    group_path: root/group[cash|all]
5. [Enabled] daily count( 21, 1 where daily high > daily greatest * 1.05 ) crossed above 2
    group_path: root/group[cash|all]
6. [Disabled] weekly count( 50, 1 where weekly volume > 1 week ago sma( close ,  5 ) * 3 ) crossed above 5
    group_path: root/group[cash|all]
7. [Disabled] daily count( 14, 1 where daily open > daily greatest * 1.02 ) crossed above 3
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( market cap > 1000 and market cap < 10000 and latest count( 21, 1 where latest high > greatest(  latest open, latest close  ) * 1.05 ) > 2 and 1 day ago  count( 21, 1 where latest high > greatest(  1 day ago  open, latest close  ) * 1.05 ) <= 2 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily market cap > 1000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily market cap < 10000 | Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 3 | 4 | Disabled | root/group[cash\|all] | daily count( 50, 1 where daily volume > 1 day ago sma( close ,  5 ) * 3 ) crossed above 5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 4 | 5 | Enabled | root/group[cash\|all] | daily count( 21, 1 where daily high > daily greatest * 1.05 ) crossed above 2 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). |
| 5 | 6 | Disabled | root/group[cash\|all] | weekly count( 50, 1 where weekly volume > 1 week ago sma( close ,  5 ) * 3 ) crossed above 5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. References weekly bars / weekly offset. |
| 6 | 7 | Disabled | root/group[cash\|all] | daily count( 14, 1 where daily open > daily greatest * 1.02 ) crossed above 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily market cap > 1000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#3** `daily market cap < 10000` — Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#5** `daily count( 21, 1 where daily high > daily greatest * 1.05 ) crossed above 2` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar).

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **3** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #4
- **Condition (verbatim):** `daily count( 50, 1 where daily volume > 1 day ago sma( close ,  5 ) * 3 ) crossed above 5`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `weekly count( 50, 1 where weekly volume > 1 week ago sma( close ,  5 ) * 3 ) crossed above 5`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. References weekly bars / weekly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `daily count( 14, 1 where daily open > daily greatest * 1.02 ) crossed above 3`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `count` — appears 4 time(s) in the expression tree
- `volume` — appears 4 time(s) in the expression tree
- `open` — appears 3 time(s) in the expression tree
- `market cap` — appears 2 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree
- `greatest` — appears 2 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 5 occurrence(s)
- `crossed above` — 4 occurrence(s)
- `*` — 4 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `1_days_ago`, `1_weeks_ago`, `5_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **3** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Fundamental, Momentum
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, timeframe:daily, timeframe:weekly
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

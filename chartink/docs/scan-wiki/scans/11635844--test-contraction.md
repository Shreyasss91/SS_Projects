---
scan_id: 11635844
scan_name: test contraction
source_url: https://chartink.com/screener/test-contraction-32
market: Indian equities
horizon: Swing
classification: ["Volatility", "Moving average", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:cash", "indicator:volume", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 8
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volatility
---

# test contraction

## Source

- Chartink URL: https://chartink.com/screener/test-contraction-32
- Scan ID: `11635844`
- Slug: `test-contraction-32`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-05-02T14:49:50.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11635844.json](../source-snapshots/11635844.json)
- Text snapshot: [source-snapshots/11635844.txt](../source-snapshots/11635844.txt)

## What this scan is for

This scan, titled "test contraction", appears designed to screen Indian equities in the **cash** universe using **5 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Volatility, Moving average, Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 2_days_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: test contraction
Scan id: 11635844
Slug: test-contraction-32
Source URL: https://chartink.com/screener/test-contraction-32
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-05-02T14:49:50.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 1000000000 * 0.1
    group_path: root/group[cash|all]
3. [Disabled] ( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3
    group_path: root/group[cash|all]
4. [Enabled] daily close > 50
    group_path: root/group[cash|all]
5. [Disabled] daily count( 3, 1 where daily high < 1 day ago high ) >= 3
6. [Disabled] daily count( 3, 1 where daily low > 1 day ago low ) >= 3
7. [Disabled] daily count( 3, 1 where daily close - daily low > 1 day ago close - 1 day ago low ) >= 3
8. [Disabled] daily count streak( 3, 1 where daily close - daily low > ( daily high - daily low ) * 0.5 ) = 3
9. [Disabled] daily sma( close ,  3 ) crossed above 1 day ago max( 21 ,  daily sma( close ,  3 ) )
10. [Disabled] daily sma( close ,  3 ) crossed above daily close * 0.01
11. [Enabled] daily count( 7, 1 where daily sma( close ,  3 ) < daily close * 0.01 ) > 6
12. [Enabled] daily sma( close ,  3 ) > 1 day ago sma( close ,  3 )
13. [Enabled] 1 day ago sma( close ,  3 ) < 2 days ago sma( close ,  3 )
14. [Disabled] daily count( 3, 1 where daily close > daily open ) >= 2

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 1000000000 * 0.1 and latest close > 50 ) ) and latest count( 7, 1 where latest sma( latest close - latest low , 3 ) < latest close * 0.01 ) > 6 and latest sma( latest close - latest low , 3 ) > 1 day ago sma( latest close - latest low , 3 ) and 1 day ago sma( latest close - latest low , 3 ) < 2 days ago sma( latest close - latest low , 3 ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | 1 day ago close * 1 day ago volume > 1000000000 * 0.1 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 3 | Disabled | ( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. ATR measures smoothed true range (volatility), not direction. |
| 4 | Enabled | daily close > 50 | Inequality test: left expression must be strictly greater than right. |
| 5 | Disabled | daily count( 3, 1 where daily high < 1 day ago high ) >= 3 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 6 | Disabled | daily count( 3, 1 where daily low > 1 day ago low ) >= 3 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 7 | Disabled | daily count( 3, 1 where daily close - daily low > 1 day ago close - 1 day ago low ) >= 3 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 8 | Disabled | daily count streak( 3, 1 where daily close - daily low > ( daily high - daily low ) * 0.5 ) = 3 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 9 | Disabled | daily sma( close ,  3 ) crossed above 1 day ago max( 21 ,  daily sma( close ,  3 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars. |
| 10 | Disabled | daily sma( close ,  3 ) crossed above daily close * 0.01 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. |
| 11 | Enabled | daily count( 7, 1 where daily sma( close ,  3 ) < daily close * 0.01 ) > 6 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 12 | Enabled | daily sma( close ,  3 ) > 1 day ago sma( close ,  3 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 13 | Enabled | 1 day ago sma( close ,  3 ) < 2 days ago sma( close ,  3 ) | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 14 | Disabled | daily count( 3, 1 where daily close > daily open ) >= 2 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 1000000000 * 0.1` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#4** `daily close > 50` — Inequality test: left expression must be strictly greater than right.
- **#11** `daily count( 7, 1 where daily sma( close ,  3 ) < daily close * 0.01 ) > 6` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#12** `daily sma( close ,  3 ) > 1 day ago sma( close ,  3 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#13** `1 day ago sma( close ,  3 ) < 2 days ago sma( close ,  3 )` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **8** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. ATR measures smoothed true range (volatility), not direction.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily count( 3, 1 where daily high < 1 day ago high ) >= 3`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `daily count( 3, 1 where daily low > 1 day ago low ) >= 3`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `daily count( 3, 1 where daily close - daily low > 1 day ago close - 1 day ago low ) >= 3`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `daily count streak( 3, 1 where daily close - daily low > ( daily high - daily low ) * 0.5 ) = 3`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `daily sma( close ,  3 ) crossed above 1 day ago max( 21 ,  daily sma( close ,  3 ) )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `daily sma( close ,  3 ) crossed above daily close * 0.01`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `daily count( 3, 1 where daily close > daily open ) >= 2`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 17 time(s) in the expression tree
- `low` — appears 14 time(s) in the expression tree
- `sma` — appears 9 time(s) in the expression tree
- `count` — appears 5 time(s) in the expression tree
- `high` — appears 3 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `avg true range` — appears 1 time(s) in the expression tree
- `count streak` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `open` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 9 occurrence(s)
- `*` — 6 occurrence(s)
- `>=` — 4 occurrence(s)
- `<` — 3 occurrence(s)
- `-` — 3 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `=` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **5** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **8** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volatility, Moving average, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:cash, indicator:volume, indicator:sma, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

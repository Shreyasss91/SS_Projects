---
scan_id: 4788899
scan_name: "Darvas Scan + Takushi + 52weekindex>75"
source_url: https://chartink.com/screener/darvas-scan-14
market: Indian equities
horizon: Multi-horizon
classification: ["Breakout", "Volume/delivery", "Volatility", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "indicator:volume", "timeframe:daily", "timeframe:weekly", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 12
disabled_filter_count: 10
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Breakout
---

# Darvas Scan + Takushi + 52weekindex>75

## Source

- Chartink URL: https://chartink.com/screener/darvas-scan-14
- Scan ID: `4788899`
- Slug: `darvas-scan-14`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2021-06-03T09:51:05.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4788899.json](../source-snapshots/4788899.json)
- Text snapshot: [source-snapshots/4788899.txt](../source-snapshots/4788899.txt)

## What this scan is for

This is a **multi-horizon** screen over **cash** with **12** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Breakout, Volume/delivery, Volatility, Momentum, Multi-factor**.
The active tests, in captured order, are:
- daily close < weekly max( 52 ,  weekly high )
- daily close < weekly max( 52 ,  weekly high ) * 0.75
- daily close > weekly min( 52 ,  weekly low ) * 1.3
- ( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 90
- daily close > weekly min( 52 ,  weekly low ) * 1.5
- [0] 15 minute count( 500, 1 where ( daily max( 500 ,  daily high ) / daily min( 500 ,  daily low ) ) < 1.1 ) >= 450
- 1 day ago open > 1 day ago close
- daily open > 1 day ago close
- daily low > 1 day ago low
- daily close > 1 day ago high
- daily open < 1 day ago open
- daily volume > 1 day ago volume

Author description (source metadata): https://www.screener.in/screens/4928/Darvas-Scan/

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Darvas Scan + Takushi + 52weekindex>75
Scan id: 4788899
Slug: darvas-scan-14
Source URL: https://chartink.com/screener/darvas-scan-14
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-03T09:51:05.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily close < weekly max( 52 ,  weekly high )
    group_path: root/group[cash|all]
3. [Enabled] daily close < weekly max( 52 ,  weekly high ) * 0.75
    group_path: root/group[cash|all]
4. [Enabled] daily close > weekly min( 52 ,  weekly low ) * 1.3
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] ( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 90
    group_path: root/group[cash|all]
7. [Disabled] ( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 75
    group_path: root/group[cash|all]
8. [Enabled] daily close > weekly min( 52 ,  weekly low ) * 1.5
    group_path: root/group[cash|all]
9. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
10. [Disabled] ( [0] 15 minute close - daily min( 22 ,  daily low ) ) * 100 / ( daily max( 22 ,  daily high ) - daily min( 22 ,  daily low ) ) crossed above 90
    group_path: root/group[cash|all]
11. [Disabled] 22 days ago close > 2 days ago close
    group_path: root/group[cash|all]
12. [Disabled] ( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 75
    group_path: root/group[cash|all]
13. [Disabled] daily close > weekly min( 52 ,  weekly low ) * 1.5
    group_path: root/group[cash|all]
14. [Disabled] [0] 15 minute count( 500, 1 where [-1] 15 minute high < [-1] 15 minute max( 550 ,  [-1] 15 minute high ) ) >= 500
    group_path: root/group[cash|all]
15. [Disabled] [0] 15 minute count( 550, 1 where [-1] 15 minute max( 550 ,  [-1] 15 minute high ) = [-24] 15 minute max( 550 ,  [-2] 15 minute high ) ) > 450
    group_path: root/group[cash|all]
16. [Disabled] [0] 15 minute close crossed above [-1] 15 minute max( 550 ,  [0] 15 minute high )
    group_path: root/group[cash|all]
17. [Disabled] daily count( 66, 1 where ( daily max( 66 ,  daily high ) / daily min( 66 ,  daily low ) ) < 1.07 ) >= 66
    group_path: root/group[cash|all]
18. [Enabled] [0] 15 minute count( 500, 1 where ( daily max( 500 ,  daily high ) / daily min( 500 ,  daily low ) ) < 1.1 ) >= 450
    group_path: root/group[cash|all]
19. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
20. [Enabled] 1 day ago open > 1 day ago close
    group_path: root/group[cash|all]
21. [Enabled] daily open > 1 day ago close
    group_path: root/group[cash|all]
22. [Enabled] daily low > 1 day ago low
    group_path: root/group[cash|all]
23. [Enabled] daily close > 1 day ago high
    group_path: root/group[cash|all]
24. [Enabled] daily open < 1 day ago open
    group_path: root/group[cash|all]
25. [Enabled] daily volume > 1 day ago volume
    group_path: root/group[cash|all]
26. [Disabled] daily volume > daily max( 50 ,  1 day ago volume )
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( [0] 15 minute count( 500, 1 where( latest max( 500 , latest high ) / latest min( 500 , latest low ) ) < 1.1 ) >= 450 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily close < weekly max( 52 ,  weekly high ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily close < weekly max( 52 ,  weekly high ) * 0.75 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily close > weekly min( 52 ,  weekly low ) * 1.3 | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 4 | 6 | Enabled | root/group[cash\|all] | ( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 90 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 5 | 7 | Disabled | root/group[cash\|all] | ( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 75 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 6 | 8 | Enabled | root/group[cash\|all] | daily close > weekly min( 52 ,  weekly low ) * 1.5 | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 7 | 10 | Disabled | root/group[cash\|all] | ( [0] 15 minute close - daily min( 22 ,  daily low ) ) * 100 / ( daily max( 22 ,  daily high ) - daily min( 22 ,  daily low ) ) crossed above 90 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 11 | Disabled | root/group[cash\|all] | 22 days ago close > 2 days ago close | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 9 | 12 | Disabled | root/group[cash\|all] | ( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 75 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 10 | 13 | Disabled | root/group[cash\|all] | daily close > weekly min( 52 ,  weekly low ) * 1.5 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 11 | 14 | Disabled | root/group[cash\|all] | [0] 15 minute count( 500, 1 where [-1] 15 minute high < [-1] 15 minute max( 550 ,  [-1] 15 minute high ) ) >= 500 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 15 | Disabled | root/group[cash\|all] | [0] 15 minute count( 550, 1 where [-1] 15 minute max( 550 ,  [-1] 15 minute high ) = [-24] 15 minute max( 550 ,  [-2] 15 minute high ) ) > 450 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 16 | Disabled | root/group[cash\|all] | [0] 15 minute close crossed above [-1] 15 minute max( 550 ,  [0] 15 minute high ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 17 | Disabled | root/group[cash\|all] | daily count( 66, 1 where ( daily max( 66 ,  daily high ) / daily min( 66 ,  daily low ) ) < 1.07 ) >= 66 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 15 | 18 | Enabled | root/group[cash\|all] | [0] 15 minute count( 500, 1 where ( daily max( 500 ,  daily high ) / daily min( 500 ,  daily low ) ) < 1.1 ) >= 450 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | 20 | Enabled | root/group[cash\|all] | 1 day ago open > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 17 | 21 | Enabled | root/group[cash\|all] | daily open > 1 day ago close | Inequality test: left expression must be strictly greater than right. |
| 18 | 22 | Enabled | root/group[cash\|all] | daily low > 1 day ago low | Inequality test: left expression must be strictly greater than right. |
| 19 | 23 | Enabled | root/group[cash\|all] | daily close > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 20 | 24 | Enabled | root/group[cash\|all] | daily open < 1 day ago open | Inequality test: left expression must be strictly less than right. |
| 21 | 25 | Enabled | root/group[cash\|all] | daily volume > 1 day ago volume | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 22 | 26 | Disabled | root/group[cash\|all] | daily volume > daily max( 50 ,  1 day ago volume ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **12** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily close < weekly max( 52 ,  weekly high )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#3** `daily close < weekly max( 52 ,  weekly high ) * 0.75` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#4** `daily close > weekly min( 52 ,  weekly low ) * 1.3` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#6** `( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 90` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#8** `daily close > weekly min( 52 ,  weekly low ) * 1.5` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#18** `[0] 15 minute count( 500, 1 where ( daily max( 500 ,  daily high ) / daily min( 500 ,  daily low ) ) < 1.1 ) >= 450` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#20** `1 day ago open > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#21** `daily open > 1 day ago close` — Inequality test: left expression must be strictly greater than right.
- **#22** `daily low > 1 day ago low` — Inequality test: left expression must be strictly greater than right.
- **#23** `daily close > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#24** `daily open < 1 day ago open` — Inequality test: left expression must be strictly less than right.
- **#25** `daily volume > 1 day ago volume` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **10** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #7
- **Condition (verbatim):** `( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 75`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `( [0] 15 minute close - daily min( 22 ,  daily low ) ) * 100 / ( daily max( 22 ,  daily high ) - daily min( 22 ,  daily low ) ) crossed above 90`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `22 days ago close > 2 days ago close`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `( daily close - weekly min( 52 ,  weekly low ) ) * 100 / ( weekly max( 52 ,  weekly high ) - weekly min( 52 ,  weekly low ) ) crossed above 75`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #13
- **Condition (verbatim):** `daily close > weekly min( 52 ,  weekly low ) * 1.5`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `[0] 15 minute count( 500, 1 where [-1] 15 minute high < [-1] 15 minute max( 550 ,  [-1] 15 minute high ) ) >= 500`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #15
- **Condition (verbatim):** `[0] 15 minute count( 550, 1 where [-1] 15 minute max( 550 ,  [-1] 15 minute high ) = [-24] 15 minute max( 550 ,  [-2] 15 minute high ) ) > 450`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `[0] 15 minute close crossed above [-1] 15 minute max( 550 ,  [0] 15 minute high )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #17
- **Condition (verbatim):** `daily count( 66, 1 where ( daily max( 66 ,  daily high ) / daily min( 66 ,  daily low ) ) < 1.07 ) >= 66`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #26
- **Condition (verbatim):** `daily volume > daily max( 50 ,  1 day ago volume )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 15 time(s) in the expression tree
- `low` — appears 15 time(s) in the expression tree
- `high` — appears 14 time(s) in the expression tree
- `max` — appears 13 time(s) in the expression tree
- `min` — appears 13 time(s) in the expression tree
- `count` — appears 4 time(s) in the expression tree
- `open` — appears 4 time(s) in the expression tree
- `volume` — appears 4 time(s) in the expression tree

### Operators observed
- `>` — 11 occurrence(s)
- `*` — 8 occurrence(s)
- `<` — 6 occurrence(s)
- `crossed above` — 5 occurrence(s)
- `/` — 4 occurrence(s)
- `>=` — 3 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `15_minute`, `1_days_ago`, `22_days_ago`, `2_days_ago`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Volume/delivery, Volatility, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **12** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **10** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Breakout, Volume/delivery, Volatility, Momentum, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, indicator:volume, timeframe:daily, timeframe:weekly, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

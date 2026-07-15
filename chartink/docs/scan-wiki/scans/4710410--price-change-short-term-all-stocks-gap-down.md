---
scan_id: 4710410
scan_name: Price Change Short term all stocks gap down
source_url: https://chartink.com/screener/price-change-short-term-all-stocks
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Momentum"]
tags: ["universe:cash","indicator:volume","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 15
disabled_filter_count: 8
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# Price Change Short term all stocks gap down

## Source

- Chartink URL: https://chartink.com/screener/price-change-short-term-all-stocks
- Scan ID: `4710410`
- Slug: `price-change-short-term-all-stocks`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-05-28T10:16:20.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4710410.json](../source-snapshots/4710410.json)
- Text snapshot: [source-snapshots/4710410.txt](../source-snapshots/4710410.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **15** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
- [0] 15 minute sum( close ,  20 ) < -4
- [0] 15 minute sum( close ,  30 ) < -4
- [0] 15 minute sum( close ,  40 ) < -4
- [0] 15 minute sum( close ,  50 ) < -4
- [0] 15 minute sum( close ,  300 ) crossed above 0
- [0] 15 minute sum( close ,  450 ) crossed above 0
- [0] 15 minute sum( close ,  600 ) crossed above 0
- [0] 15 minute sum( close ,  750 ) crossed above 0
- [0] 15 minute sum( close ,  300 ) crossed below -30
- [0] 15 minute sum( close ,  450 ) crossed below -30
- [0] 15 minute sum( close ,  600 ) crossed below -30
- [0] 15 minute sum( close ,  750 ) crossed below -30
- ( [0] 15 minute sum( close ,  20 ) + [0] 15 minute sum( close ,  30 ) + [0] 15 minute sum( close ,  40 ) + [0] 15 minute sum( close ,  50 ) ) / 4 > ( ( daily square( [0] 15 minute sum( close ,  20 ) + daily square( [0] 15 minute sum( close ,  30 ) + daily square( [0] 15 minute sum( close ,  40 ) + daily square( [0] 15 minute sum( close ,  50 ) ) / 4 ) / 2 ) ) ) )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Price Change Short term all stocks gap down
Scan id: 4710410
Slug: price-change-short-term-all-stocks
Source URL: https://chartink.com/screener/price-change-short-term-all-stocks
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-05-28T10:16:20.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
    group_path: root/group[cash|all]
4. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
5. [Disabled] [0] 15 minute sum( close ,  300 ) crossed below -11
    group_path: root/group[cash|any]
6. [Disabled] [0] 1 minute sum( close ,  300 ) crossed below -1
    group_path: root/group[cash|any]
7. [Enabled] [0] 15 minute sum( close ,  20 ) < -4
    group_path: root/group[cash|any]
8. [Enabled] [0] 15 minute sum( close ,  30 ) < -4
    group_path: root/group[cash|any]
9. [Enabled] [0] 15 minute sum( close ,  40 ) < -4
    group_path: root/group[cash|any]
10. [Enabled] [0] 15 minute sum( close ,  50 ) < -4
    group_path: root/group[cash|any]
11. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
12. [Disabled] [0] 15 minute sum( close ,  300 ) crossed below -11
    group_path: root/group[cash|any]
13. [Disabled] [0] 1 minute sum( close ,  300 ) crossed below -1
    group_path: root/group[cash|any]
14. [Enabled] [0] 15 minute sum( close ,  300 ) crossed above 0
    group_path: root/group[cash|any]
15. [Enabled] [0] 15 minute sum( close ,  450 ) crossed above 0
    group_path: root/group[cash|any]
16. [Enabled] [0] 15 minute sum( close ,  600 ) crossed above 0
    group_path: root/group[cash|any]
17. [Enabled] [0] 15 minute sum( close ,  750 ) crossed above 0
    group_path: root/group[cash|any]
18. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
19. [Disabled] [0] 15 minute sum( close ,  300 ) crossed below -11
    group_path: root/group[cash|any]
20. [Disabled] [0] 1 minute sum( close ,  300 ) crossed below -1
    group_path: root/group[cash|any]
21. [Enabled] [0] 15 minute sum( close ,  300 ) crossed below -30
    group_path: root/group[cash|any]
22. [Enabled] [0] 15 minute sum( close ,  450 ) crossed below -30
    group_path: root/group[cash|any]
23. [Enabled] [0] 15 minute sum( close ,  600 ) crossed below -30
    group_path: root/group[cash|any]
24. [Enabled] [0] 15 minute sum( close ,  750 ) crossed below -30
    group_path: root/group[cash|any]
25. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
26. [Enabled] ( [0] 15 minute sum( close ,  20 ) + [0] 15 minute sum( close ,  30 ) + [0] 15 minute sum( close ,  40 ) + [0] 15 minute sum( close ,  50 ) ) / 4 > ( ( daily square( [0] 15 minute sum( close ,  20 ) + daily square( [0] 15 minute sum( close ,  30 ) + daily square( [0] 15 minute sum( close ,  40 ) + daily square( [0] 15 minute sum( close ,  50 ) ) / 4 ) / 2 ) ) ) )
    group_path: root/group[cash|all]
27. [Disabled] [0] 15 minute open > [-1] 15 minute close * 1.01
28. [Disabled] [0] 15 minute open < [-1] 15 minute close * 0.99

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and latest count( 200, 1 where( latest high / latest low ) = 1 ) < 1 ) ) and( cash ( [0] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) < -30 and [ -1 ] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 300 ) >= -30 or [0] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 450 ) < -30 and [ -1 ] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 450 ) >= -30 or [0] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 600 ) < -30 and [ -1 ] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 600 ) >= -30 or [0] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 750 ) < -30 and [ -1 ] 15 minute sum( [0] 15 minute "close - 1 candle ago close / 1 candle ago close * 100" , 750 ) >= -30 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1 | Inequality test: left expression must be strictly less than right. |
| 3 | 5 | Disabled | root/group[cash\|any] | [0] 15 minute sum( close ,  300 ) crossed below -11 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 6 | Disabled | root/group[cash\|any] | [0] 1 minute sum( close ,  300 ) crossed below -1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 7 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  20 ) < -4 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 8 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  30 ) < -4 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 9 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  40 ) < -4 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 10 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  50 ) < -4 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 12 | Disabled | root/group[cash\|any] | [0] 15 minute sum( close ,  300 ) crossed below -11 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 13 | Disabled | root/group[cash\|any] | [0] 1 minute sum( close ,  300 ) crossed below -1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 14 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  300 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 15 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  450 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 16 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  600 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 17 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  750 ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 19 | Disabled | root/group[cash\|any] | [0] 15 minute sum( close ,  300 ) crossed below -11 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | 20 | Disabled | root/group[cash\|any] | [0] 1 minute sum( close ,  300 ) crossed below -1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 17 | 21 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  300 ) crossed below -30 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 18 | 22 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  450 ) crossed below -30 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 19 | 23 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  600 ) crossed below -30 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 20 | 24 | Enabled | root/group[cash\|any] | [0] 15 minute sum( close ,  750 ) crossed below -30 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 21 | 26 | Enabled | root/group[cash\|all] | ( [0] 15 minute sum( close ,  20 ) + [0] 15 minute sum( close ,  30 ) + [0] 15 minute sum( close ,  40 ) + [0] 15 minute sum( close ,  50 ) ) / 4 > ( ( daily square( [0] 15 minute sum( close ,  20 ) + daily square( [0] 15 minute sum( close ,  30 ) + daily square( [0] 15 minute sum( close ,  40 ) + daily square( [0] 15 minute sum( close ,  50 ) ) / 4 ) / 2 ) ) ) ) | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 22 | 27 | Disabled | root | [0] 15 minute open > [-1] 15 minute close * 1.01 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 23 | 28 | Disabled | root | [0] 15 minute open < [-1] 15 minute close * 0.99 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **15** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1` — Inequality test: left expression must be strictly less than right.
- **#7** `[0] 15 minute sum( close ,  20 ) < -4` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[0] 15 minute sum( close ,  30 ) < -4` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[0] 15 minute sum( close ,  40 ) < -4` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[0] 15 minute sum( close ,  50 ) < -4` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#14** `[0] 15 minute sum( close ,  300 ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#15** `[0] 15 minute sum( close ,  450 ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#16** `[0] 15 minute sum( close ,  600 ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#17** `[0] 15 minute sum( close ,  750 ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#21** `[0] 15 minute sum( close ,  300 ) crossed below -30` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#22** `[0] 15 minute sum( close ,  450 ) crossed below -30` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#23** `[0] 15 minute sum( close ,  600 ) crossed below -30` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#24** `[0] 15 minute sum( close ,  750 ) crossed below -30` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#26** `( [0] 15 minute sum( close ,  20 ) + [0] 15 minute sum( close ,  30 ) + [0] 15 minute sum( close ,  40 ) + [0] 15 minute sum( close ,  50 ) ) / 4 > ( ( daily square( [0] 15 minute sum( close ,  20 ) + daily square( [0] 15 minute sum( close ,  30 ) + daily square( [0] 15 minute sum( close ,  40 ) + daily square( [0] 15 minute sum( close ,  50 ) ) / 4 ) / 2 ) ) ) )` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **8** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #5
- **Condition (verbatim):** `[0] 15 minute sum( close ,  300 ) crossed below -11`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `[0] 1 minute sum( close ,  300 ) crossed below -1`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `[0] 15 minute sum( close ,  300 ) crossed below -11`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #13
- **Condition (verbatim):** `[0] 1 minute sum( close ,  300 ) crossed below -1`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #19
- **Condition (verbatim):** `[0] 15 minute sum( close ,  300 ) crossed below -11`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #20
- **Condition (verbatim):** `[0] 1 minute sum( close ,  300 ) crossed below -1`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #27
- **Condition (verbatim):** `[0] 15 minute open > [-1] 15 minute close * 1.01`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #28
- **Condition (verbatim):** `[0] 15 minute open < [-1] 15 minute close * 0.99`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `sum` — appears 26 time(s) in the expression tree
- `% change` — appears 23 time(s) in the expression tree
- `close` — appears 12 time(s) in the expression tree
- `square` — appears 4 time(s) in the expression tree
- `open` — appears 2 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed below` — 10 occurrence(s)
- `<` — 6 occurrence(s)
- `crossed above` — 4 occurrence(s)
- `*` — 3 occurrence(s)
- `>` — 3 occurrence(s)
- `=` — 1 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_days_ago`, `1_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Momentum, Price action, Volume/delivery, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **15** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **8** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Momentum
- **Tags:** universe:cash, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 4663438
scan_name: Sideways after downfall
source_url: https://chartink.com/screener/sideways-after-downfall
market: Indian equities
horizon: Intraday
classification: ["Breakout", "Volume/delivery", "Volatility", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "indicator:volume", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 28
disabled_filter_count: 3
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Breakout
---

# Sideways after downfall

## Source

- Chartink URL: https://chartink.com/screener/sideways-after-downfall
- Scan ID: `4663438`
- Slug: `sideways-after-downfall`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-05-24T14:37:27.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4663438.json](../source-snapshots/4663438.json)
- Text snapshot: [source-snapshots/4663438.txt](../source-snapshots/4663438.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **28** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Breakout, Volume/delivery, Volatility, Momentum, Multi-factor**.
The active tests, in captured order, are:
- 1 day ago close * 1 day ago volume > 100000000
- daily high crossed above 20 days ago max( 750 ,  daily high )
- 20 days ago max( 480 ,  daily high ) < 500 days ago max( 500 ,  daily high )
- 1 day ago close * 1 day ago volume > 100000000
- daily high crossed above 1 day ago max( 750 ,  daily high )
- 1 day ago max( 499 ,  daily high ) < 500 days ago max( 500 ,  daily high )
- 1 day ago close * 1 day ago volume > 100000000
- daily max( 30 ,  daily high ) crossed below 31 days ago max( 30 ,  daily high )
- 31 days ago max( 30 ,  daily high ) < 61 days ago max( 30 ,  daily high )
- 61 days ago max( 30 ,  daily high ) < 91 days ago max( 30 ,  daily high )
- 1 day ago close * 1 day ago volume > 100000000
- daily min( 30 ,  daily low ) crossed below 31 days ago min( 30 ,  daily low )
- 31 days ago min( 30 ,  daily low ) < 61 days ago min( 30 ,  daily low )
- 1 day ago close * 1 day ago volume > 100000000
- daily min( 20 ,  daily low ) > 21 days ago min( 20 ,  daily low )
- 21 days ago min( 20 ,  daily low ) crossed below 41 days ago min( 20 ,  daily low )
- 41 days ago min( 20 ,  daily low ) < 61 days ago min( 20 ,  daily low )
- 61 days ago min( 20 ,  daily low ) < 81 days ago min( 20 ,  daily low )
- 1 day ago close * 1 day ago volume > 100000000
- [0] 15 minute min( 20 ,  [0] 15 minute low ) > [-21] 15 minute min( 20 ,  [0] 15 minute low )
- [-21] 15 minute min( 20 ,  [0] 15 minute low ) crossed below [-41] 15 minute min( 20 ,  [0] 15 minute low )
- [-41] 15 minute min( 20 ,  [0] 15 minute low ) < [-61] 15 minute min( 20 ,  [0] 15 minute low )
- [-61] 15 minute min( 20 ,  [0] 15 minute low ) < [-81] 15 minute min( 20 ,  [0] 15 minute low )
- 1 day ago close * 1 day ago volume > 100000000
- [0] 15 minute min( 30 ,  [0] 15 minute low ) > [-31] 15 minute min( 30 ,  [0] 15 minute low )
- [-31] 15 minute min( 30 ,  [0] 15 minute low ) crossed below [-61] 15 minute min( 30 ,  [0] 15 minute low )
- [-61] 15 minute min( 30 ,  [0] 15 minute low ) < [-91] 15 minute min( 30 ,  [0] 15 minute low )
- [-91] 15 minute min( 30 ,  [0] 15 minute low ) < [-121] 15 minute min( 30 ,  [0] 15 minute low )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Sideways after downfall
Scan id: 4663438
Slug: sideways-after-downfall
Source URL: https://chartink.com/screener/sideways-after-downfall
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-05-24T14:37:27.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] daily high crossed above 20 days ago max( 750 ,  daily high )
    group_path: root/group[cash|all]
4. [Enabled] 20 days ago max( 480 ,  daily high ) < 500 days ago max( 500 ,  daily high )
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
7. [Enabled] daily high crossed above 1 day ago max( 750 ,  daily high )
    group_path: root/group[cash|all]
8. [Enabled] 1 day ago max( 499 ,  daily high ) < 500 days ago max( 500 ,  daily high )
    group_path: root/group[cash|all]
9. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
10. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
11. [Enabled] daily max( 30 ,  daily high ) crossed below 31 days ago max( 30 ,  daily high )
    group_path: root/group[cash|all]
12. [Enabled] 31 days ago max( 30 ,  daily high ) < 61 days ago max( 30 ,  daily high )
    group_path: root/group[cash|all]
13. [Enabled] 61 days ago max( 30 ,  daily high ) < 91 days ago max( 30 ,  daily high )
    group_path: root/group[cash|all]
14. [Disabled] 91 days ago max( 30 ,  daily high ) < 121 days ago max( 30 ,  daily high )
    group_path: root/group[cash|all]
15. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
16. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
17. [Enabled] daily min( 30 ,  daily low ) crossed below 31 days ago min( 30 ,  daily low )
    group_path: root/group[cash|all]
18. [Enabled] 31 days ago min( 30 ,  daily low ) < 61 days ago min( 30 ,  daily low )
    group_path: root/group[cash|all]
19. [Disabled] 61 days ago min( 30 ,  daily low ) < 91 days ago min( 30 ,  daily low )
    group_path: root/group[cash|all]
20. [Disabled] 91 days ago min( 30 ,  daily low ) < 121 days ago min( 30 ,  daily low )
    group_path: root/group[cash|all]
21. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
22. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
23. [Enabled] daily min( 20 ,  daily low ) > 21 days ago min( 20 ,  daily low )
    group_path: root/group[cash|all]
24. [Enabled] 21 days ago min( 20 ,  daily low ) crossed below 41 days ago min( 20 ,  daily low )
    group_path: root/group[cash|all]
25. [Enabled] 41 days ago min( 20 ,  daily low ) < 61 days ago min( 20 ,  daily low )
    group_path: root/group[cash|all]
26. [Enabled] 61 days ago min( 20 ,  daily low ) < 81 days ago min( 20 ,  daily low )
    group_path: root/group[cash|all]
27. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
28. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
29. [Enabled] [0] 15 minute min( 20 ,  [0] 15 minute low ) > [-21] 15 minute min( 20 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
30. [Enabled] [-21] 15 minute min( 20 ,  [0] 15 minute low ) crossed below [-41] 15 minute min( 20 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
31. [Enabled] [-41] 15 minute min( 20 ,  [0] 15 minute low ) < [-61] 15 minute min( 20 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
32. [Enabled] [-61] 15 minute min( 20 ,  [0] 15 minute low ) < [-81] 15 minute min( 20 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
33. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
34. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
35. [Enabled] [0] 15 minute min( 30 ,  [0] 15 minute low ) > [-31] 15 minute min( 30 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
36. [Enabled] [-31] 15 minute min( 30 ,  [0] 15 minute low ) crossed below [-61] 15 minute min( 30 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
37. [Enabled] [-61] 15 minute min( 30 ,  [0] 15 minute low ) < [-91] 15 minute min( 30 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
38. [Enabled] [-91] 15 minute min( 30 ,  [0] 15 minute low ) < [-121] 15 minute min( 30 ,  [0] 15 minute low )
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 15 minute min( 30 , [0] 15 minute low ) > [-31] 15 minute min( 30 , [0] 15 minute low ) and [-31] 15 minute min( 30 , [0] 15 minute low ) < [-61] 15 minute min( 30 , [0] 15 minute low ) and [ -32 ] 15 minute min( 30 , [0] 15 minute low )>= [ -62 ] 15 minute min( 30 , [0] 15 minute low ) and [-61] 15 minute min( 30 , [0] 15 minute low ) < [-91] 15 minute min( 30 , [0] 15 minute low ) and [-91] 15 minute min( 30 , [0] 15 minute low ) < [-121] 15 minute min( 30 , [0] 15 minute low ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily high crossed above 20 days ago max( 750 ,  daily high ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. |
| 3 | 4 | Enabled | root/group[cash\|all] | 20 days ago max( 480 ,  daily high ) < 500 days ago max( 500 ,  daily high ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. |
| 4 | 6 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 5 | 7 | Enabled | root/group[cash\|all] | daily high crossed above 1 day ago max( 750 ,  daily high ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. |
| 6 | 8 | Enabled | root/group[cash\|all] | 1 day ago max( 499 ,  daily high ) < 500 days ago max( 500 ,  daily high ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. |
| 7 | 10 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 8 | 11 | Enabled | root/group[cash\|all] | daily max( 30 ,  daily high ) crossed below 31 days ago max( 30 ,  daily high ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). max(N, series) is the highest value of series over N bars. |
| 9 | 12 | Enabled | root/group[cash\|all] | 31 days ago max( 30 ,  daily high ) < 61 days ago max( 30 ,  daily high ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. |
| 10 | 13 | Enabled | root/group[cash\|all] | 61 days ago max( 30 ,  daily high ) < 91 days ago max( 30 ,  daily high ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. |
| 11 | 14 | Disabled | root/group[cash\|all] | 91 days ago max( 30 ,  daily high ) < 121 days ago max( 30 ,  daily high ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 12 | 16 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 13 | 17 | Enabled | root/group[cash\|all] | daily min( 30 ,  daily low ) crossed below 31 days ago min( 30 ,  daily low ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 14 | 18 | Enabled | root/group[cash\|all] | 31 days ago min( 30 ,  daily low ) < 61 days ago min( 30 ,  daily low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |
| 15 | 19 | Disabled | root/group[cash\|all] | 61 days ago min( 30 ,  daily low ) < 91 days ago min( 30 ,  daily low ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. |
| 16 | 20 | Disabled | root/group[cash\|all] | 91 days ago min( 30 ,  daily low ) < 121 days ago min( 30 ,  daily low ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. |
| 17 | 22 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 18 | 23 | Enabled | root/group[cash\|all] | daily min( 20 ,  daily low ) > 21 days ago min( 20 ,  daily low ) | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |
| 19 | 24 | Enabled | root/group[cash\|all] | 21 days ago min( 20 ,  daily low ) crossed below 41 days ago min( 20 ,  daily low ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 20 | 25 | Enabled | root/group[cash\|all] | 41 days ago min( 20 ,  daily low ) < 61 days ago min( 20 ,  daily low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |
| 21 | 26 | Enabled | root/group[cash\|all] | 61 days ago min( 20 ,  daily low ) < 81 days ago min( 20 ,  daily low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |
| 22 | 28 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 23 | 29 | Enabled | root/group[cash\|all] | [0] 15 minute min( 20 ,  [0] 15 minute low ) > [-21] 15 minute min( 20 ,  [0] 15 minute low ) | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 24 | 30 | Enabled | root/group[cash\|all] | [-21] 15 minute min( 20 ,  [0] 15 minute low ) crossed below [-41] 15 minute min( 20 ,  [0] 15 minute low ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 25 | 31 | Enabled | root/group[cash\|all] | [-41] 15 minute min( 20 ,  [0] 15 minute low ) < [-61] 15 minute min( 20 ,  [0] 15 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 26 | 32 | Enabled | root/group[cash\|all] | [-61] 15 minute min( 20 ,  [0] 15 minute low ) < [-81] 15 minute min( 20 ,  [0] 15 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 27 | 34 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 28 | 35 | Enabled | root/group[cash\|all] | [0] 15 minute min( 30 ,  [0] 15 minute low ) > [-31] 15 minute min( 30 ,  [0] 15 minute low ) | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 29 | 36 | Enabled | root/group[cash\|all] | [-31] 15 minute min( 30 ,  [0] 15 minute low ) crossed below [-61] 15 minute min( 30 ,  [0] 15 minute low ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 30 | 37 | Enabled | root/group[cash\|all] | [-61] 15 minute min( 30 ,  [0] 15 minute low ) < [-91] 15 minute min( 30 ,  [0] 15 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 31 | 38 | Enabled | root/group[cash\|all] | [-91] 15 minute min( 30 ,  [0] 15 minute low ) < [-121] 15 minute min( 30 ,  [0] 15 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **28** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `daily high crossed above 20 days ago max( 750 ,  daily high )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars.
- **#4** `20 days ago max( 480 ,  daily high ) < 500 days ago max( 500 ,  daily high )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars.
- **#6** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#7** `daily high crossed above 1 day ago max( 750 ,  daily high )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars.
- **#8** `1 day ago max( 499 ,  daily high ) < 500 days ago max( 500 ,  daily high )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars.
- **#10** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#11** `daily max( 30 ,  daily high ) crossed below 31 days ago max( 30 ,  daily high )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). max(N, series) is the highest value of series over N bars.
- **#12** `31 days ago max( 30 ,  daily high ) < 61 days ago max( 30 ,  daily high )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars.
- **#13** `61 days ago max( 30 ,  daily high ) < 91 days ago max( 30 ,  daily high )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars.
- **#16** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#17** `daily min( 30 ,  daily low ) crossed below 31 days ago min( 30 ,  daily low )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#18** `31 days ago min( 30 ,  daily low ) < 61 days ago min( 30 ,  daily low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.
- **#22** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#23** `daily min( 20 ,  daily low ) > 21 days ago min( 20 ,  daily low )` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.
- **#24** `21 days ago min( 20 ,  daily low ) crossed below 41 days ago min( 20 ,  daily low )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#25** `41 days ago min( 20 ,  daily low ) < 61 days ago min( 20 ,  daily low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.
- **#26** `61 days ago min( 20 ,  daily low ) < 81 days ago min( 20 ,  daily low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.
- **#28** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#29** `[0] 15 minute min( 20 ,  [0] 15 minute low ) > [-21] 15 minute min( 20 ,  [0] 15 minute low )` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#30** `[-21] 15 minute min( 20 ,  [0] 15 minute low ) crossed below [-41] 15 minute min( 20 ,  [0] 15 minute low )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#31** `[-41] 15 minute min( 20 ,  [0] 15 minute low ) < [-61] 15 minute min( 20 ,  [0] 15 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#32** `[-61] 15 minute min( 20 ,  [0] 15 minute low ) < [-81] 15 minute min( 20 ,  [0] 15 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#34** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#35** `[0] 15 minute min( 30 ,  [0] 15 minute low ) > [-31] 15 minute min( 30 ,  [0] 15 minute low )` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#36** `[-31] 15 minute min( 30 ,  [0] 15 minute low ) crossed below [-61] 15 minute min( 30 ,  [0] 15 minute low )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#37** `[-61] 15 minute min( 30 ,  [0] 15 minute low ) < [-91] 15 minute min( 30 ,  [0] 15 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#38** `[-91] 15 minute min( 30 ,  [0] 15 minute low ) < [-121] 15 minute min( 30 ,  [0] 15 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **3** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #14
- **Condition (verbatim):** `91 days ago max( 30 ,  daily high ) < 121 days ago max( 30 ,  daily high )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #19
- **Condition (verbatim):** `61 days ago min( 30 ,  daily low ) < 91 days ago min( 30 ,  daily low )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #20
- **Condition (verbatim):** `91 days ago min( 30 ,  daily low ) < 121 days ago min( 30 ,  daily low )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `min` — appears 32 time(s) in the expression tree
- `low` — appears 32 time(s) in the expression tree
- `high` — appears 16 time(s) in the expression tree
- `max` — appears 14 time(s) in the expression tree
- `close` — appears 7 time(s) in the expression tree
- `volume` — appears 7 time(s) in the expression tree

### Operators observed
- `<` — 14 occurrence(s)
- `>` — 10 occurrence(s)
- `*` — 7 occurrence(s)
- `crossed below` — 5 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `121_days_ago`, `15_minute`, `1_days_ago`, `20_days_ago`, `21_days_ago`, `31_days_ago`, `41_days_ago`, `500_days_ago`, `61_days_ago`, `81_days_ago`, `91_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Volume/delivery, Volatility, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **28** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **3** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Breakout, Volume/delivery, Volatility, Momentum, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

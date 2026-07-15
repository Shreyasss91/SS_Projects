---
scan_id: 4934183
scan_name: "Retest old low after long time 90%"
source_url: https://chartink.com/screener/retest-old-low-after-long-time-90
market: Indian equities
horizon: Intraday
classification: ["Volume/delivery", "Breakout", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "indicator:volume", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 27
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: any
primary_classification: Volume/delivery
---

# Retest old low after long time 90%

## Source

- Chartink URL: https://chartink.com/screener/retest-old-low-after-long-time-90
- Scan ID: `4934183`
- Slug: `retest-old-low-after-long-time-90`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-06-12T19:03:34.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4934183.json](../source-snapshots/4934183.json)
- Text snapshot: [source-snapshots/4934183.txt](../source-snapshots/4934183.txt)

## What this scan is for

This is a **intraday** screen over **futures** with **27** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Volume/delivery, Breakout, Momentum, Multi-factor**.
The active tests, in captured order, are:
- 1 day ago close * 1 day ago volume > 100000000
- daily low crossed below 20 days ago min( 750 ,  daily low )
- 20 days ago min( 480 ,  daily low ) < 500 days ago min( 500 ,  daily low )
- 1 day ago close * 1 day ago volume > 100000000
- daily low crossed below 1 day ago min( 750 ,  daily low )
- 1 day ago min( 499 ,  daily low ) < 500 days ago min( 500 ,  daily low )
- 1 day ago close * 1 day ago volume > 100000000
- [0] 15 minute low crossed below [-1] 15 minute min( 500 ,  [0] 15 minute low )
- [-1] 15 minute min( 499 ,  [0] 15 minute low ) < [-500] 15 minute min( 500 ,  [0] 15 minute low )
- 1 day ago close * 1 day ago volume > 100000000
- [0] 15 minute low crossed below [-1] 15 minute min( 500 ,  [0] 15 minute low ) * 1.01
- [-1] 15 minute min( 499 ,  [0] 15 minute low ) < [-500] 15 minute min( 500 ,  [0] 15 minute low )
- 1 day ago close * 1 day ago volume > 100000000
- [0] 30 minute low crossed below [-1] 30 minute min( 500 ,  [0] 30 minute low ) * 1.02
- [-1] 30 minute min( 499 ,  [0] 30 minute low ) < [-500] 30 minute min( 500 ,  [0] 30 minute low )
- 1 day ago close * 1 day ago volume > 100000000
- [0] 60 minute low crossed below [-1] 60 minute min( 500 ,  [0] 60 minute low ) * 1.04
- [-1] 60 minute min( 499 ,  [0] 60 minute low ) < [-500] 60 minute min( 500 ,  [0] 60 minute low )
- 1 day ago close * 1 day ago volume > 100000000
- [0] 120 minute low crossed below [-1] 120 minute min( 500 ,  [0] 120 minute low ) * 1.08
- [-1] 120 minute min( 499 ,  [0] 120 minute low ) < [-500] 120 minute min( 500 ,  [0] 120 minute low )
- 1 day ago close * 1 day ago volume > 100000000
- [0] 240 minute low crossed below [-1] 240 minute min( 500 ,  [0] 240 minute low ) * 1.16
- [-1] 240 minute min( 499 ,  [0] 240 minute low ) < [-500] 240 minute min( 500 ,  [0] 240 minute low )
- 1 day ago close * 1 day ago volume > 100000000
- daily low crossed below 1 day ago min( 500 ,  daily low ) * 1.24
- 1 day ago min( 499 ,  1 day ago low ) < 500 days ago min( 500 ,  500 days ago low )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Retest old low after long time 90%
Scan id: 4934183
Slug: retest-old-low-after-long-time-90
Source URL: https://chartink.com/screener/retest-old-low-after-long-time-90
Root universe/segment: futures
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-12T19:03:34.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] daily low crossed below 20 days ago min( 750 ,  daily low )
    group_path: root/group[cash|all]
4. [Enabled] 20 days ago min( 480 ,  daily low ) < 500 days ago min( 500 ,  daily low )
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
7. [Enabled] daily low crossed below 1 day ago min( 750 ,  daily low )
    group_path: root/group[cash|all]
8. [Enabled] 1 day ago min( 499 ,  daily low ) < 500 days ago min( 500 ,  daily low )
    group_path: root/group[cash|all]
9. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
10. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
11. [Enabled] [0] 15 minute low crossed below [-1] 15 minute min( 500 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
12. [Enabled] [-1] 15 minute min( 499 ,  [0] 15 minute low ) < [-500] 15 minute min( 500 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
13. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
15. [Enabled] [0] 15 minute low crossed below [-1] 15 minute min( 500 ,  [0] 15 minute low ) * 1.01
    group_path: root/group[cash|all]
16. [Enabled] [-1] 15 minute min( 499 ,  [0] 15 minute low ) < [-500] 15 minute min( 500 ,  [0] 15 minute low )
    group_path: root/group[cash|all]
17. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
18. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
19. [Enabled] [0] 30 minute low crossed below [-1] 30 minute min( 500 ,  [0] 30 minute low ) * 1.02
    group_path: root/group[cash|all]
20. [Enabled] [-1] 30 minute min( 499 ,  [0] 30 minute low ) < [-500] 30 minute min( 500 ,  [0] 30 minute low )
    group_path: root/group[cash|all]
21. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
22. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
23. [Enabled] [0] 60 minute low crossed below [-1] 60 minute min( 500 ,  [0] 60 minute low ) * 1.04
    group_path: root/group[cash|all]
24. [Enabled] [-1] 60 minute min( 499 ,  [0] 60 minute low ) < [-500] 60 minute min( 500 ,  [0] 60 minute low )
    group_path: root/group[cash|all]
25. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
26. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
27. [Enabled] [0] 120 minute low crossed below [-1] 120 minute min( 500 ,  [0] 120 minute low ) * 1.08
    group_path: root/group[cash|all]
28. [Enabled] [-1] 120 minute min( 499 ,  [0] 120 minute low ) < [-500] 120 minute min( 500 ,  [0] 120 minute low )
    group_path: root/group[cash|all]
29. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
30. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
31. [Enabled] [0] 240 minute low crossed below [-1] 240 minute min( 500 ,  [0] 240 minute low ) * 1.16
    group_path: root/group[cash|all]
32. [Enabled] [-1] 240 minute min( 499 ,  [0] 240 minute low ) < [-500] 240 minute min( 500 ,  [0] 240 minute low )
    group_path: root/group[cash|all]
33. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
34. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
35. [Enabled] daily low crossed below 1 day ago min( 500 ,  daily low ) * 1.24
    group_path: root/group[cash|all]
36. [Enabled] 1 day ago min( 499 ,  1 day ago low ) < 500 days ago min( 500 ,  500 days ago low )
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 15 minute low < [-1] 15 minute min( 500 , [0] 15 minute low ) * 1.01 and [ -1 ] 15 minute low >= [ -2 ] 15 minute min( 500 , [0] 15 minute low )* 1.01 and [-1] 15 minute min( 499 , [0] 15 minute low ) < [-500] 15 minute min( 500 , [0] 15 minute low ) ) ) or( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 30 minute low < [-1] 30 minute min( 500 , [0] 30 minute low ) * 1.02 and [ -1 ] 30 minute low >= [ -2 ] 30 minute min( 500 , [0] 30 minute low )* 1.02 and [-1] 30 minute min( 499 , [0] 30 minute low ) < [-500] 30 minute min( 500 , [0] 30 minute low ) ) ) or( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 1 hour low < [-1] 1 hour min( 500 , [0] 1 hour low ) * 1.04 and [ -1 ] 1 hour low >= [ -2 ] 1 hour min( 500 , [0] 1 hour low )* 1.04 and [-1] 1 hour min( 499 , [0] 1 hour low ) < [-500] 1 hour min( 500 , [0] 1 hour low ) ) ) or( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 2 hour low < [-1] 2 hour min( 500 , [0] 2 hour low ) * 1.08 and [ -1 ] 2 hour low >= [ -2 ] 2 hour min( 500 , [0] 2 hour low )* 1.08 and [-1] 2 hour min( 499 , [0] 2 hour low ) < [-500] 2 hour min( 500 , [0] 2 hour low ) ) ) or( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 4 hour low < [-1] 4 hour min( 500 , [0] 4 hour low ) * 1.16 and [ -1 ] 4 hour low >= [ -2 ] 4 hour min( 500 , [0] 4 hour low )* 1.16 and [-1] 4 hour min( 499 , [0] 4 hour low ) < [-500] 4 hour min( 500 , [0] 4 hour low ) ) ) or( cash ( 1 day ago close * 1 day ago volume > 100000000 and latest low < 1 day ago min( 500 , latest low ) * 1.24 and 1 day ago  low >= 2 day ago  min( 500 , latest low )* 1.24 and 1 day ago min( 499 , 1 day ago low ) < 500 days ago min( 500 , 500 days ago low ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily low crossed below 20 days ago min( 750 ,  daily low ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 3 | 4 | Enabled | root/group[cash\|all] | 20 days ago min( 480 ,  daily low ) < 500 days ago min( 500 ,  daily low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |
| 4 | 6 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 5 | 7 | Enabled | root/group[cash\|all] | daily low crossed below 1 day ago min( 750 ,  daily low ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 6 | 8 | Enabled | root/group[cash\|all] | 1 day ago min( 499 ,  daily low ) < 500 days ago min( 500 ,  daily low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |
| 7 | 10 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 8 | 11 | Enabled | root/group[cash\|all] | [0] 15 minute low crossed below [-1] 15 minute min( 500 ,  [0] 15 minute low ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 12 | Enabled | root/group[cash\|all] | [-1] 15 minute min( 499 ,  [0] 15 minute low ) < [-500] 15 minute min( 500 ,  [0] 15 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 14 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 11 | 15 | Enabled | root/group[cash\|all] | [0] 15 minute low crossed below [-1] 15 minute min( 500 ,  [0] 15 minute low ) * 1.01 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 16 | Enabled | root/group[cash\|all] | [-1] 15 minute min( 499 ,  [0] 15 minute low ) < [-500] 15 minute min( 500 ,  [0] 15 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 18 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 14 | 19 | Enabled | root/group[cash\|all] | [0] 30 minute low crossed below [-1] 30 minute min( 500 ,  [0] 30 minute low ) * 1.02 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 20 | Enabled | root/group[cash\|all] | [-1] 30 minute min( 499 ,  [0] 30 minute low ) < [-500] 30 minute min( 500 ,  [0] 30 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | 22 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 17 | 23 | Enabled | root/group[cash\|all] | [0] 60 minute low crossed below [-1] 60 minute min( 500 ,  [0] 60 minute low ) * 1.04 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 18 | 24 | Enabled | root/group[cash\|all] | [-1] 60 minute min( 499 ,  [0] 60 minute low ) < [-500] 60 minute min( 500 ,  [0] 60 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 19 | 26 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 20 | 27 | Enabled | root/group[cash\|all] | [0] 120 minute low crossed below [-1] 120 minute min( 500 ,  [0] 120 minute low ) * 1.08 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 21 | 28 | Enabled | root/group[cash\|all] | [-1] 120 minute min( 499 ,  [0] 120 minute low ) < [-500] 120 minute min( 500 ,  [0] 120 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 22 | 30 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 23 | 31 | Enabled | root/group[cash\|all] | [0] 240 minute low crossed below [-1] 240 minute min( 500 ,  [0] 240 minute low ) * 1.16 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 24 | 32 | Enabled | root/group[cash\|all] | [-1] 240 minute min( 499 ,  [0] 240 minute low ) < [-500] 240 minute min( 500 ,  [0] 240 minute low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 25 | 34 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 26 | 35 | Enabled | root/group[cash\|all] | daily low crossed below 1 day ago min( 500 ,  daily low ) * 1.24 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 27 | 36 | Enabled | root/group[cash\|all] | 1 day ago min( 499 ,  1 day ago low ) < 500 days ago min( 500 ,  500 days ago low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **27** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `daily low crossed below 20 days ago min( 750 ,  daily low )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#4** `20 days ago min( 480 ,  daily low ) < 500 days ago min( 500 ,  daily low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.
- **#6** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#7** `daily low crossed below 1 day ago min( 750 ,  daily low )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#8** `1 day ago min( 499 ,  daily low ) < 500 days ago min( 500 ,  daily low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.
- **#10** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#11** `[0] 15 minute low crossed below [-1] 15 minute min( 500 ,  [0] 15 minute low )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#12** `[-1] 15 minute min( 499 ,  [0] 15 minute low ) < [-500] 15 minute min( 500 ,  [0] 15 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#14** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#15** `[0] 15 minute low crossed below [-1] 15 minute min( 500 ,  [0] 15 minute low ) * 1.01` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#16** `[-1] 15 minute min( 499 ,  [0] 15 minute low ) < [-500] 15 minute min( 500 ,  [0] 15 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#18** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#19** `[0] 30 minute low crossed below [-1] 30 minute min( 500 ,  [0] 30 minute low ) * 1.02` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#20** `[-1] 30 minute min( 499 ,  [0] 30 minute low ) < [-500] 30 minute min( 500 ,  [0] 30 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#22** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#23** `[0] 60 minute low crossed below [-1] 60 minute min( 500 ,  [0] 60 minute low ) * 1.04` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#24** `[-1] 60 minute min( 499 ,  [0] 60 minute low ) < [-500] 60 minute min( 500 ,  [0] 60 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#26** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#27** `[0] 120 minute low crossed below [-1] 120 minute min( 500 ,  [0] 120 minute low ) * 1.08` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#28** `[-1] 120 minute min( 499 ,  [0] 120 minute low ) < [-500] 120 minute min( 500 ,  [0] 120 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#30** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#31** `[0] 240 minute low crossed below [-1] 240 minute min( 500 ,  [0] 240 minute low ) * 1.16` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#32** `[-1] 240 minute min( 499 ,  [0] 240 minute low ) < [-500] 240 minute min( 500 ,  [0] 240 minute low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#34** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#35** `daily low crossed below 1 day ago min( 500 ,  daily low ) * 1.24` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#36** `1 day ago min( 499 ,  1 day ago low ) < 500 days ago min( 500 ,  500 days ago low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `low` — appears 36 time(s) in the expression tree
- `min` — appears 27 time(s) in the expression tree
- `close` — appears 9 time(s) in the expression tree
- `volume` — appears 9 time(s) in the expression tree

### Operators observed
- `*` — 15 occurrence(s)
- `>` — 9 occurrence(s)
- `crossed below` — 9 occurrence(s)
- `<` — 9 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **futures**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `120_minute`, `15_minute`, `1_days_ago`, `20_days_ago`, `21_days_ago`, `240_minute`, `30_minute`, `500_days_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Breakout, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **27** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Breakout, Momentum, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** futures
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

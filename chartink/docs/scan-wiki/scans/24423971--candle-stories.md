---
scan_id: 24423971
scan_name: Candle Stories
source_url: https://chartink.com/screener/halt-candle-7
market: Indian equities
horizon: "Swing"
classification: ["Moving average","Volume/delivery","Breakout","Momentum"]
tags: ["universe:nifty-200","indicator:sma","indicator:volume","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 48
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# Candle Stories

## Source

- Chartink URL: https://chartink.com/screener/halt-candle-7
- Scan ID: `24423971`
- Slug: `halt-candle-7`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2025-11-09T04:57:42.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24423971.json](../source-snapshots/24423971.json)
- Text snapshot: [source-snapshots/24423971.txt](../source-snapshots/24423971.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **48** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Breakout, Momentum**.

The active tests, in captured order:
- daily open < 1 day ago close * 0.99
- daily close < 1 day ago close
- daily close < 1 day ago low
- daily close > daily open
- 1 day ago count( 3, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.2 ) >= 1
- daily high < 1 day ago low + ( 0.6 * ( 1 day ago high - 1 day ago low ) )
- daily low < 1 day ago low
- daily close < 1 day ago close
- daily high > 1 day ago high
- daily low < 1 day ago low
- daily close < daily open
- daily close < 1 day ago close
- 1 day ago close > 1 day ago open
- daily high < 1 day ago high
- daily low < 1 day ago low
- 1 day ago high > 2 days ago high
- 1 day ago low > 2 days ago low
- daily count( 3, 1 where daily close < daily open ) >= 2
- daily high > 1 day ago high
- daily low > 1 day ago low
- 1 day ago high < 2 days ago high
- 1 day ago low < 2 days ago low
- daily count( 3, 1 where daily close > daily open ) >= 2
- daily max( 6 ,  daily close ) < 6 days ago high
- daily min( 6 ,  daily close ) > 6 days ago low
- daily count( 6, 1 where daily close < daily open ) >= 2
- daily count( 6, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.1 ) >= 2
- daily close crossed below 1 day ago min( 6 ,  daily close )
- daily high > 1 day ago min( 6 ,  daily low ) + ( .8 * ( 1 day ago max( 6 ,  daily high ) - 1 day ago min( 6 ,  daily low ) ) )
- daily close < daily open
- 1 day ago close > 1 day ago open
- daily high > 1 day ago high
- daily low < 1 day ago low
- daily abs( daily close - daily open ) > daily abs( 1 day ago close - 1 day ago open )
- daily HLC3 < 1 day ago HLC3
- daily open < 1 day ago close
- daily open < 1 day ago open
- daily open < 1 day ago HLC3
- daily abs( 1 day ago high - 1 day ago open ) / daily abs( 1 day ago high - 1 day ago low ) < 0.05
- daily abs( 1 day ago close - 1 day ago open ) / daily abs( 1 day ago high - 1 day ago low ) > 0.8
- daily abs( 1 day ago close - 1 day ago open ) > 2 days ago sma( close ,  6 ) * 1.5
- daily count streak( 3, 1 where daily high > 1 day ago high ) = 3
- daily count streak( 3, 1 where daily low > 1 day ago low ) = 3
- daily count streak( 3, 1 where daily close > 1 day ago close ) = 3
- daily count streak( 3, 1 where daily volume > 1 day ago volume ) = 3
- daily abs( 1 - ( ( daily high - daily low ) / ( 1 day ago high - 1 day ago low ) ) ) < 0.005
- daily abs( 1 - ( ( daily high ) / ( 1 day ago high ) ) ) < 0.001
- daily abs( 1 - ( ( daily low ) / ( 1 day ago low ) ) ) < 0.001

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Candle Stories
Scan id: 24423971
Slug: halt-candle-7
Source URL: https://chartink.com/screener/halt-candle-7
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-09T04:57:42.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily open < 1 day ago close * 0.99
    group_path: root/group[cash|all]
3. [Enabled] daily close < 1 day ago close
    group_path: root/group[cash|all]
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all])
5. [Enabled] daily close < 1 day ago low
    group_path: root/group[cash|all]/group[cash|all]
6. [Enabled] daily close > daily open
    group_path: root/group[cash|all]/group[cash|all]
7. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Enabled] 1 day ago count( 3, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.2 ) >= 1
    group_path: root/group[cash|all]
9. [Disabled] daily open < 1 day ago close * 0.995
    group_path: root/group[cash|all]
10. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all])
11. [Enabled] daily high < 1 day ago low + ( 0.6 * ( 1 day ago high - 1 day ago low ) )
    group_path: root/group[cash|all]/group[cash|all]
12. [Enabled] daily low < 1 day ago low
    group_path: root/group[cash|all]/group[cash|all]
13. [Enabled] daily close < 1 day ago close
    group_path: root/group[cash|all]/group[cash|all]
14. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
15. [Enabled] daily high > 1 day ago high
    group_path: root/group[cash|all]
16. [Enabled] daily low < 1 day ago low
    group_path: root/group[cash|all]
17. [Enabled] daily close < daily open
    group_path: root/group[cash|all]
18. [Enabled] daily close < 1 day ago close
    group_path: root/group[cash|all]
19. [Enabled] 1 day ago close > 1 day ago open
    group_path: root/group[cash|all]
20. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
21. [Enabled] daily high < 1 day ago high
    group_path: root/group[cash|all]
22. [Enabled] daily low < 1 day ago low
    group_path: root/group[cash|all]
23. [Enabled] 1 day ago high > 2 days ago high
    group_path: root/group[cash|all]
24. [Enabled] 1 day ago low > 2 days ago low
    group_path: root/group[cash|all]
25. [Enabled] daily count( 3, 1 where daily close < daily open ) >= 2
    group_path: root/group[cash|all]
26. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
27. [Enabled] daily high > 1 day ago high
    group_path: root/group[cash|all]
28. [Enabled] daily low > 1 day ago low
    group_path: root/group[cash|all]
29. [Enabled] 1 day ago high < 2 days ago high
    group_path: root/group[cash|all]
30. [Enabled] 1 day ago low < 2 days ago low
    group_path: root/group[cash|all]
31. [Enabled] daily count( 3, 1 where daily close > daily open ) >= 2
    group_path: root/group[cash|all]
32. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
33. [Enabled] daily max( 6 ,  daily close ) < 6 days ago high
    group_path: root/group[cash|all]
34. [Enabled] daily min( 6 ,  daily close ) > 6 days ago low
    group_path: root/group[cash|all]
35. [Enabled] daily count( 6, 1 where daily close < daily open ) >= 2
    group_path: root/group[cash|all]
36. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
37. [Enabled] daily count( 6, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.1 ) >= 2
    group_path: root/group[cash|all]
38. [Disabled] daily count( 3, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.1 ) >= 3
    group_path: root/group[cash|all]
39. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
40. [Enabled] daily close crossed below 1 day ago min( 6 ,  daily close )
    group_path: root/group[cash|all]
41. [Enabled] daily high > 1 day ago min( 6 ,  daily low ) + ( .8 * ( 1 day ago max( 6 ,  daily high ) - 1 day ago min( 6 ,  daily low ) ) )
    group_path: root/group[cash|all]
42. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
43. [Enabled] daily close < daily open
    group_path: root/group[cash|all]
44. [Enabled] 1 day ago close > 1 day ago open
    group_path: root/group[cash|all]
45. [Enabled] daily high > 1 day ago high
    group_path: root/group[cash|all]
46. [Enabled] daily low < 1 day ago low
    group_path: root/group[cash|all]
47. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all])
48. [Enabled] daily abs( daily close - daily open ) > daily abs( 1 day ago close - 1 day ago open )
    group_path: root/group[cash|all]/group[cash|all]
49. [Enabled] daily HLC3 < 1 day ago HLC3
    group_path: root/group[cash|all]/group[cash|all]
50. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all]/group[cash|all])
51. [Enabled] daily open < 1 day ago close
    group_path: root/group[cash|all]/group[cash|all]/group[cash|all]
52. [Enabled] daily open < 1 day ago open
    group_path: root/group[cash|all]/group[cash|all]/group[cash|all]
53. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
54. [Enabled] daily open < 1 day ago HLC3
    group_path: root/group[cash|all]
55. [Enabled] daily abs( 1 day ago high - 1 day ago open ) / daily abs( 1 day ago high - 1 day ago low ) < 0.05
    group_path: root/group[cash|all]
56. [Enabled] daily abs( 1 day ago close - 1 day ago open ) / daily abs( 1 day ago high - 1 day ago low ) > 0.8
    group_path: root/group[cash|all]
57. [Enabled] daily abs( 1 day ago close - 1 day ago open ) > 2 days ago sma( close ,  6 ) * 1.5
    group_path: root/group[cash|all]
58. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
59. [Enabled] daily count streak( 3, 1 where daily high > 1 day ago high ) = 3
    group_path: root/group[cash|all]
60. [Enabled] daily count streak( 3, 1 where daily low > 1 day ago low ) = 3
    group_path: root/group[cash|all]
61. [Enabled] daily count streak( 3, 1 where daily close > 1 day ago close ) = 3
    group_path: root/group[cash|all]
62. [Enabled] daily count streak( 3, 1 where daily volume > 1 day ago volume ) = 3
    group_path: root/group[cash|all]
63. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
64. [Enabled] daily abs( 1 - ( ( daily high - daily low ) / ( 1 day ago high - 1 day ago low ) ) ) < 0.005
    group_path: root/group[cash|all]
65. [Enabled] daily abs( 1 - ( ( daily high ) / ( 1 day ago high ) ) ) < 0.001
    group_path: root/group[cash|all]
66. [Enabled] daily abs( 1 - ( ( daily low ) / ( 1 day ago low ) ) ) < 0.001
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( abs( 1 - ( ( daily high - daily low ) / ( 1 day ago high - 1 day ago low ) ) ) < 0.005 and abs( 1 - ( ( daily high ) / ( 1 day ago high ) ) ) < 0.001 and abs( 1 - ( ( daily low ) / ( 1 day ago low ) ) ) < 0.001 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily open < 1 day ago close * 0.99 | Inequality test: left expression must be strictly less than right. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily close < 1 day ago close | Inequality test: left expression must be strictly less than right. |
| 3 | 5 | Enabled | root/group[cash\|all]/group[cash\|all] | daily close < 1 day ago low | Inequality test: left expression must be strictly less than right. |
| 4 | 6 | Enabled | root/group[cash\|all]/group[cash\|all] | daily close > daily open | Inequality test: left expression must be strictly greater than right. |
| 5 | 8 | Enabled | root/group[cash\|all] | 1 day ago count( 3, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.2 ) >= 1 | Inequality test: left expression must be strictly less than right. |
| 6 | 9 | Disabled | root/group[cash\|all] | daily open < 1 day ago close * 0.995 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 7 | 11 | Enabled | root/group[cash\|all]/group[cash\|all] | daily high < 1 day ago low + ( 0.6 * ( 1 day ago high - 1 day ago low ) ) | Inequality test: left expression must be strictly less than right. |
| 8 | 12 | Enabled | root/group[cash\|all]/group[cash\|all] | daily low < 1 day ago low | Inequality test: left expression must be strictly less than right. |
| 9 | 13 | Enabled | root/group[cash\|all]/group[cash\|all] | daily close < 1 day ago close | Inequality test: left expression must be strictly less than right. |
| 10 | 15 | Enabled | root/group[cash\|all] | daily high > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 11 | 16 | Enabled | root/group[cash\|all] | daily low < 1 day ago low | Inequality test: left expression must be strictly less than right. |
| 12 | 17 | Enabled | root/group[cash\|all] | daily close < daily open | Inequality test: left expression must be strictly less than right. |
| 13 | 18 | Enabled | root/group[cash\|all] | daily close < 1 day ago close | Inequality test: left expression must be strictly less than right. |
| 14 | 19 | Enabled | root/group[cash\|all] | 1 day ago close > 1 day ago open | Inequality test: left expression must be strictly greater than right. |
| 15 | 21 | Enabled | root/group[cash\|all] | daily high < 1 day ago high | Inequality test: left expression must be strictly less than right. |
| 16 | 22 | Enabled | root/group[cash\|all] | daily low < 1 day ago low | Inequality test: left expression must be strictly less than right. |
| 17 | 23 | Enabled | root/group[cash\|all] | 1 day ago high > 2 days ago high | Inequality test: left expression must be strictly greater than right. |
| 18 | 24 | Enabled | root/group[cash\|all] | 1 day ago low > 2 days ago low | Inequality test: left expression must be strictly greater than right. |
| 19 | 25 | Enabled | root/group[cash\|all] | daily count( 3, 1 where daily close < daily open ) >= 2 | Inequality test: left expression must be strictly less than right. |
| 20 | 27 | Enabled | root/group[cash\|all] | daily high > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 21 | 28 | Enabled | root/group[cash\|all] | daily low > 1 day ago low | Inequality test: left expression must be strictly greater than right. |
| 22 | 29 | Enabled | root/group[cash\|all] | 1 day ago high < 2 days ago high | Inequality test: left expression must be strictly less than right. |
| 23 | 30 | Enabled | root/group[cash\|all] | 1 day ago low < 2 days ago low | Inequality test: left expression must be strictly less than right. |
| 24 | 31 | Enabled | root/group[cash\|all] | daily count( 3, 1 where daily close > daily open ) >= 2 | Inequality test: left expression must be strictly greater than right. |
| 25 | 33 | Enabled | root/group[cash\|all] | daily max( 6 ,  daily close ) < 6 days ago high | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. |
| 26 | 34 | Enabled | root/group[cash\|all] | daily min( 6 ,  daily close ) > 6 days ago low | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |
| 27 | 35 | Enabled | root/group[cash\|all] | daily count( 6, 1 where daily close < daily open ) >= 2 | Inequality test: left expression must be strictly less than right. |
| 28 | 37 | Enabled | root/group[cash\|all] | daily count( 6, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.1 ) >= 2 | Inequality test: left expression must be strictly less than right. |
| 29 | 38 | Disabled | root/group[cash\|all] | daily count( 3, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.1 ) >= 3 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 30 | 40 | Enabled | root/group[cash\|all] | daily close crossed below 1 day ago min( 6 ,  daily close ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 31 | 41 | Enabled | root/group[cash\|all] | daily high > 1 day ago min( 6 ,  daily low ) + ( .8 * ( 1 day ago max( 6 ,  daily high ) - 1 day ago min( 6 ,  daily low ) ) ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 32 | 43 | Enabled | root/group[cash\|all] | daily close < daily open | Inequality test: left expression must be strictly less than right. |
| 33 | 44 | Enabled | root/group[cash\|all] | 1 day ago close > 1 day ago open | Inequality test: left expression must be strictly greater than right. |
| 34 | 45 | Enabled | root/group[cash\|all] | daily high > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 35 | 46 | Enabled | root/group[cash\|all] | daily low < 1 day ago low | Inequality test: left expression must be strictly less than right. |
| 36 | 48 | Enabled | root/group[cash\|all]/group[cash\|all] | daily abs( daily close - daily open ) > daily abs( 1 day ago close - 1 day ago open ) | Inequality test: left expression must be strictly greater than right. |
| 37 | 49 | Enabled | root/group[cash\|all]/group[cash\|all] | daily HLC3 < 1 day ago HLC3 | Inequality test: left expression must be strictly less than right. |
| 38 | 51 | Enabled | root/group[cash\|all]/group[cash\|all]/group[cash\|all] | daily open < 1 day ago close | Inequality test: left expression must be strictly less than right. |
| 39 | 52 | Enabled | root/group[cash\|all]/group[cash\|all]/group[cash\|all] | daily open < 1 day ago open | Inequality test: left expression must be strictly less than right. |
| 40 | 54 | Enabled | root/group[cash\|all] | daily open < 1 day ago HLC3 | Inequality test: left expression must be strictly less than right. |
| 41 | 55 | Enabled | root/group[cash\|all] | daily abs( 1 day ago high - 1 day ago open ) / daily abs( 1 day ago high - 1 day ago low ) < 0.05 | Inequality test: left expression must be strictly less than right. |
| 42 | 56 | Enabled | root/group[cash\|all] | daily abs( 1 day ago close - 1 day ago open ) / daily abs( 1 day ago high - 1 day ago low ) > 0.8 | Inequality test: left expression must be strictly greater than right. |
| 43 | 57 | Enabled | root/group[cash\|all] | daily abs( 1 day ago close - 1 day ago open ) > 2 days ago sma( close ,  6 ) * 1.5 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 44 | 59 | Enabled | root/group[cash\|all] | daily count streak( 3, 1 where daily high > 1 day ago high ) = 3 | Inequality test: left expression must be strictly greater than right. |
| 45 | 60 | Enabled | root/group[cash\|all] | daily count streak( 3, 1 where daily low > 1 day ago low ) = 3 | Inequality test: left expression must be strictly greater than right. |
| 46 | 61 | Enabled | root/group[cash\|all] | daily count streak( 3, 1 where daily close > 1 day ago close ) = 3 | Inequality test: left expression must be strictly greater than right. |
| 47 | 62 | Enabled | root/group[cash\|all] | daily count streak( 3, 1 where daily volume > 1 day ago volume ) = 3 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 48 | 64 | Enabled | root/group[cash\|all] | daily abs( 1 - ( ( daily high - daily low ) / ( 1 day ago high - 1 day ago low ) ) ) < 0.005 | Inequality test: left expression must be strictly less than right. |
| 49 | 65 | Enabled | root/group[cash\|all] | daily abs( 1 - ( ( daily high ) / ( 1 day ago high ) ) ) < 0.001 | Inequality test: left expression must be strictly less than right. |
| 50 | 66 | Enabled | root/group[cash\|all] | daily abs( 1 - ( ( daily low ) / ( 1 day ago low ) ) ) < 0.001 | Inequality test: left expression must be strictly less than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **48** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily open < 1 day ago close * 0.99` — Inequality test: left expression must be strictly less than right.
- **#3** `daily close < 1 day ago close` — Inequality test: left expression must be strictly less than right.
- **#5** `daily close < 1 day ago low` — Inequality test: left expression must be strictly less than right.
- **#6** `daily close > daily open` — Inequality test: left expression must be strictly greater than right.
- **#8** `1 day ago count( 3, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.2 ) >= 1` — Inequality test: left expression must be strictly less than right.
- **#11** `daily high < 1 day ago low + ( 0.6 * ( 1 day ago high - 1 day ago low ) )` — Inequality test: left expression must be strictly less than right.
- **#12** `daily low < 1 day ago low` — Inequality test: left expression must be strictly less than right.
- **#13** `daily close < 1 day ago close` — Inequality test: left expression must be strictly less than right.
- **#15** `daily high > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#16** `daily low < 1 day ago low` — Inequality test: left expression must be strictly less than right.
- **#17** `daily close < daily open` — Inequality test: left expression must be strictly less than right.
- **#18** `daily close < 1 day ago close` — Inequality test: left expression must be strictly less than right.
- **#19** `1 day ago close > 1 day ago open` — Inequality test: left expression must be strictly greater than right.
- **#21** `daily high < 1 day ago high` — Inequality test: left expression must be strictly less than right.
- **#22** `daily low < 1 day ago low` — Inequality test: left expression must be strictly less than right.
- **#23** `1 day ago high > 2 days ago high` — Inequality test: left expression must be strictly greater than right.
- **#24** `1 day ago low > 2 days ago low` — Inequality test: left expression must be strictly greater than right.
- **#25** `daily count( 3, 1 where daily close < daily open ) >= 2` — Inequality test: left expression must be strictly less than right.
- **#27** `daily high > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#28** `daily low > 1 day ago low` — Inequality test: left expression must be strictly greater than right.
- **#29** `1 day ago high < 2 days ago high` — Inequality test: left expression must be strictly less than right.
- **#30** `1 day ago low < 2 days ago low` — Inequality test: left expression must be strictly less than right.
- **#31** `daily count( 3, 1 where daily close > daily open ) >= 2` — Inequality test: left expression must be strictly greater than right.
- **#33** `daily max( 6 ,  daily close ) < 6 days ago high` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars.
- **#34** `daily min( 6 ,  daily close ) > 6 days ago low` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.
- **#35** `daily count( 6, 1 where daily close < daily open ) >= 2` — Inequality test: left expression must be strictly less than right.
- **#37** `daily count( 6, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.1 ) >= 2` — Inequality test: left expression must be strictly less than right.
- **#40** `daily close crossed below 1 day ago min( 6 ,  daily close )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#41** `daily high > 1 day ago min( 6 ,  daily low ) + ( .8 * ( 1 day ago max( 6 ,  daily high ) - 1 day ago min( 6 ,  daily low ) ) )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#43** `daily close < daily open` — Inequality test: left expression must be strictly less than right.
- **#44** `1 day ago close > 1 day ago open` — Inequality test: left expression must be strictly greater than right.
- **#45** `daily high > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#46** `daily low < 1 day ago low` — Inequality test: left expression must be strictly less than right.
- **#48** `daily abs( daily close - daily open ) > daily abs( 1 day ago close - 1 day ago open )` — Inequality test: left expression must be strictly greater than right.
- **#49** `daily HLC3 < 1 day ago HLC3` — Inequality test: left expression must be strictly less than right.
- **#51** `daily open < 1 day ago close` — Inequality test: left expression must be strictly less than right.
- **#52** `daily open < 1 day ago open` — Inequality test: left expression must be strictly less than right.
- **#54** `daily open < 1 day ago HLC3` — Inequality test: left expression must be strictly less than right.
- **#55** `daily abs( 1 day ago high - 1 day ago open ) / daily abs( 1 day ago high - 1 day ago low ) < 0.05` — Inequality test: left expression must be strictly less than right.
- **#56** `daily abs( 1 day ago close - 1 day ago open ) / daily abs( 1 day ago high - 1 day ago low ) > 0.8` — Inequality test: left expression must be strictly greater than right.
- **#57** `daily abs( 1 day ago close - 1 day ago open ) > 2 days ago sma( close ,  6 ) * 1.5` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#59** `daily count streak( 3, 1 where daily high > 1 day ago high ) = 3` — Inequality test: left expression must be strictly greater than right.
- **#60** `daily count streak( 3, 1 where daily low > 1 day ago low ) = 3` — Inequality test: left expression must be strictly greater than right.
- **#61** `daily count streak( 3, 1 where daily close > 1 day ago close ) = 3` — Inequality test: left expression must be strictly greater than right.
- **#62** `daily count streak( 3, 1 where daily volume > 1 day ago volume ) = 3` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#64** `daily abs( 1 - ( ( daily high - daily low ) / ( 1 day ago high - 1 day ago low ) ) ) < 0.005` — Inequality test: left expression must be strictly less than right.
- **#65** `daily abs( 1 - ( ( daily high ) / ( 1 day ago high ) ) ) < 0.001` — Inequality test: left expression must be strictly less than right.
- **#66** `daily abs( 1 - ( ( daily low ) / ( 1 day ago low ) ) ) < 0.001` — Inequality test: left expression must be strictly less than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #9
- **Condition (verbatim):** `daily open < 1 day ago close * 0.995`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #38
- **Condition (verbatim):** `daily count( 3, 1 where daily abs( daily close - daily open ) / ( daily high - daily low ) < 0.1 ) >= 3`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 32 time(s) in the expression tree
- `low` — appears 31 time(s) in the expression tree
- `high` — appears 29 time(s) in the expression tree
- `open` — appears 23 time(s) in the expression tree
- `abs` — appears 14 time(s) in the expression tree
- `count` — appears 6 time(s) in the expression tree
- `min` — appears 4 time(s) in the expression tree
- `count streak` — appears 4 time(s) in the expression tree
- `custom_indicator_4583` — appears 3 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 30 occurrence(s)
- `>` — 19 occurrence(s)
- `>=` — 6 occurrence(s)
- `/` — 5 occurrence(s)
- `=` — 4 occurrence(s)
- `*` — 3 occurrence(s)
- `+` — 2 occurrence(s)
- `crossed below` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `6_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **48** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Moving average, Volume/delivery, Breakout, Momentum
- **Tags:** universe:nifty-200, indicator:sma, indicator:volume, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

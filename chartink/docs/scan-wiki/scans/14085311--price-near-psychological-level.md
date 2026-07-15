---
scan_id: 14085311
scan_name: price near psychological level
source_url: https://chartink.com/screener/price-near-psychological-level
market: Indian equities
horizon: Intraday
classification: ["Other"]
tags: ["universe:futures", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 60
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: any
primary_classification: Other
---

# price near psychological level

## Source

- Chartink URL: https://chartink.com/screener/price-near-psychological-level
- Scan ID: `14085311`
- Slug: `price-near-psychological-level`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-12-06T12:09:07.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14085311.json](../source-snapshots/14085311.json)
- Text snapshot: [source-snapshots/14085311.txt](../source-snapshots/14085311.txt)

## What this scan is for

This scan, titled "price near psychological level", appears designed to screen Indian equities in the **futures** universe using **60 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Other**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `1_days_ago, 5_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: price near psychological level
Scan id: 14085311
Slug: price-near-psychological-level
Source URL: https://chartink.com/screener/price-near-psychological-level
Root universe/segment: futures
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-06T12:09:07.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] [0] 5 minute low < 100
    group_path: root/group[cash|all]
3. [Enabled] [-1] 5 minute low > 100
    group_path: root/group[cash|all]
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] [0] 5 minute low < 200
    group_path: root/group[cash|all]
6. [Enabled] [-1] 5 minute low > 200
    group_path: root/group[cash|all]
7. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Enabled] [0] 5 minute low < 300
    group_path: root/group[cash|all]
9. [Enabled] [-1] 5 minute low > 300
    group_path: root/group[cash|all]
10. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
11. [Enabled] [0] 5 minute low < 400
    group_path: root/group[cash|all]
12. [Enabled] [-1] 5 minute low > 400
    group_path: root/group[cash|all]
13. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Enabled] [0] 5 minute low < 500
    group_path: root/group[cash|all]
15. [Enabled] [-1] 5 minute low > 500
    group_path: root/group[cash|all]
16. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
17. [Enabled] [0] 5 minute low < 600
    group_path: root/group[cash|all]
18. [Enabled] [-1] 5 minute low > 600
    group_path: root/group[cash|all]
19. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
20. [Enabled] [0] 5 minute low < 700
    group_path: root/group[cash|all]
21. [Enabled] [-1] 5 minute low > 700
    group_path: root/group[cash|all]
22. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
23. [Enabled] [0] 5 minute low < 800
    group_path: root/group[cash|all]
24. [Enabled] [-1] 5 minute low > 800
    group_path: root/group[cash|all]
25. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
26. [Enabled] [0] 5 minute low < 900
    group_path: root/group[cash|all]
27. [Enabled] [-1] 5 minute low > 900
    group_path: root/group[cash|all]
28. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
29. [Enabled] [0] 5 minute low < 1000
    group_path: root/group[cash|all]
30. [Enabled] [-1] 5 minute low > 1000
    group_path: root/group[cash|all]
31. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
32. [Enabled] [0] 5 minute low < 1100
    group_path: root/group[cash|all]
33. [Enabled] [-1] 5 minute low > 1100
    group_path: root/group[cash|all]
34. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
35. [Enabled] [0] 5 minute low < 1200
    group_path: root/group[cash|all]
36. [Enabled] [-1] 5 minute low > 1200
    group_path: root/group[cash|all]
37. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
38. [Enabled] [0] 5 minute low < 1300
    group_path: root/group[cash|all]
39. [Enabled] [-1] 5 minute low > 1300
    group_path: root/group[cash|all]
40. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
41. [Enabled] [0] 5 minute low < 1400
    group_path: root/group[cash|all]
42. [Enabled] [-1] 5 minute low > 1400
    group_path: root/group[cash|all]
43. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
44. [Enabled] [0] 5 minute low < 1500
    group_path: root/group[cash|all]
45. [Enabled] [-1] 5 minute low > 1500
    group_path: root/group[cash|all]
46. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
47. [Enabled] [0] 5 minute low < 1600
    group_path: root/group[cash|all]
48. [Enabled] [-1] 5 minute low > 1600
    group_path: root/group[cash|all]
49. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
50. [Enabled] [0] 5 minute low < 1700
    group_path: root/group[cash|all]
51. [Enabled] [-1] 5 minute low > 1700
    group_path: root/group[cash|all]
52. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
53. [Enabled] [0] 5 minute low < 1800
    group_path: root/group[cash|all]
54. [Enabled] [-1] 5 minute low > 1800
    group_path: root/group[cash|all]
55. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
56. [Enabled] [0] 5 minute low < 1900
    group_path: root/group[cash|all]
57. [Enabled] [-1] 5 minute low > 1900
    group_path: root/group[cash|all]
58. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
59. [Enabled] [0] 5 minute low < 2000
    group_path: root/group[cash|all]
60. [Enabled] [-1] 5 minute low > 2000
    group_path: root/group[cash|all]
61. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
62. [Enabled] [0] 5 minute low < 2100
    group_path: root/group[cash|all]
63. [Enabled] [-1] 5 minute low > 2100
    group_path: root/group[cash|all]
64. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
65. [Enabled] [0] 5 minute low < 2200
    group_path: root/group[cash|all]
66. [Enabled] [-1] 5 minute low > 2200
    group_path: root/group[cash|all]
67. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
68. [Enabled] [0] 5 minute low < 2300
    group_path: root/group[cash|all]
69. [Enabled] [-1] 5 minute low > 2300
    group_path: root/group[cash|all]
70. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
71. [Enabled] [0] 5 minute low < 2400
    group_path: root/group[cash|all]
72. [Enabled] [-1] 5 minute low > 2400
    group_path: root/group[cash|all]
73. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
74. [Enabled] [0] 5 minute low < 2500
    group_path: root/group[cash|all]
75. [Enabled] [-1] 5 minute low > 2500
    group_path: root/group[cash|all]
76. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
77. [Enabled] [0] 5 minute low < 2600
    group_path: root/group[cash|all]
78. [Enabled] [-1] 5 minute low > 2600
    group_path: root/group[cash|all]
79. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
80. [Enabled] [0] 5 minute low < 2700
    group_path: root/group[cash|all]
81. [Enabled] [-1] 5 minute low > 2700
    group_path: root/group[cash|all]
82. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
83. [Enabled] [0] 5 minute low < 2800
    group_path: root/group[cash|all]
84. [Enabled] [-1] 5 minute low > 2800
    group_path: root/group[cash|all]
85. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
86. [Enabled] [0] 5 minute low < 2900
    group_path: root/group[cash|all]
87. [Enabled] [-1] 5 minute low > 2900
    group_path: root/group[cash|all]
88. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
89. [Enabled] [0] 5 minute low < 3000
    group_path: root/group[cash|all]
90. [Enabled] [-1] 5 minute low > 3000
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( ( cash ( [0] 5 minute low < 100 and [-1] 5 minute low > 100 ) ) or( cash ( [0] 5 minute low < 200 and [-1] 5 minute low > 200 ) ) or( cash ( [0] 5 minute low < 300 and [-1] 5 minute low > 300 ) ) or( cash ( [0] 5 minute low < 400 and [-1] 5 minute low > 400 ) ) or( cash ( [0] 5 minute low < 500 and [-1] 5 minute low > 500 ) ) or( cash ( [0] 5 minute low < 600 and [-1] 5 minute low > 600 ) ) or( cash ( [0] 5 minute low < 700 and [-1] 5 minute low > 700 ) ) or( cash ( [0] 5 minute low < 800 and [-1] 5 minute low > 800 ) ) or( cash ( [0] 5 minute low < 900 and [-1] 5 minute low > 900 ) ) or( cash ( [0] 5 minute low < 1000 and [-1] 5 minute low > 1000 ) ) or( cash ( [0] 5 minute low < 1100 and [-1] 5 minute low > 1100 ) ) or( cash ( [0] 5 minute low < 1200 and [-1] 5 minute low > 1200 ) ) or( cash ( [0] 5 minute low < 1300 and [-1] 5 minute low > 1300 ) ) or( cash ( [0] 5 minute low < 1400 and [-1] 5 minute low > 1400 ) ) or( cash ( [0] 5 minute low < 1500 and [-1] 5 minute low > 1500 ) ) or( cash ( [0] 5 minute low < 1600 and [-1] 5 minute low > 1600 ) ) or( cash ( [0] 5 minute low < 1700 and [-1] 5 minute low > 1700 ) ) or( cash ( [0] 5 minute low < 1800 and [-1] 5 minute low > 1800 ) ) or( cash ( [0] 5 minute low < 1900 and [-1] 5 minute low > 1900 ) ) or( cash ( [0] 5 minute low < 2000 and [-1] 5 minute low > 2000 ) ) or( cash ( [0] 5 minute low < 2100 and [-1] 5 minute low > 2100 ) ) or( cash ( [0] 5 minute low < 2200 and [-1] 5 minute low > 2200 ) ) or( cash ( [0] 5 minute low < 2300 and [-1] 5 minute low > 2300 ) ) or( cash ( [0] 5 minute low < 2400 and [-1] 5 minute low > 2400 ) ) or( cash ( [0] 5 minute low < 2500 and [-1] 5 minute low > 2500 ) ) or( cash ( [0] 5 minute low < 2600 and [-1] 5 minute low > 2600 ) ) or( cash ( [0] 5 minute low < 2700 and [-1] 5 minute low > 2700 ) ) or( cash ( [0] 5 minute low < 2800 and [-1] 5 minute low > 2800 ) ) or( cash ( [0] 5 minute low < 2900 and [-1] 5 minute low > 2900 ) ) or( cash ( [0] 5 minute low < 3000 and [-1] 5 minute low > 3000 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | [0] 5 minute low < 100 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | Enabled | [-1] 5 minute low > 100 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 5 | Enabled | [0] 5 minute low < 200 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | Enabled | [-1] 5 minute low > 200 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 8 | Enabled | [0] 5 minute low < 300 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | Enabled | [-1] 5 minute low > 300 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 11 | Enabled | [0] 5 minute low < 400 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | Enabled | [-1] 5 minute low > 400 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 14 | Enabled | [0] 5 minute low < 500 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | Enabled | [-1] 5 minute low > 500 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 17 | Enabled | [0] 5 minute low < 600 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 18 | Enabled | [-1] 5 minute low > 600 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 19 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 20 | Enabled | [0] 5 minute low < 700 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 21 | Enabled | [-1] 5 minute low > 700 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 22 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 23 | Enabled | [0] 5 minute low < 800 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 24 | Enabled | [-1] 5 minute low > 800 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 25 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 26 | Enabled | [0] 5 minute low < 900 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 27 | Enabled | [-1] 5 minute low > 900 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 28 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 29 | Enabled | [0] 5 minute low < 1000 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 30 | Enabled | [-1] 5 minute low > 1000 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 31 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 32 | Enabled | [0] 5 minute low < 1100 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 33 | Enabled | [-1] 5 minute low > 1100 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 34 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 35 | Enabled | [0] 5 minute low < 1200 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 36 | Enabled | [-1] 5 minute low > 1200 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 37 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 38 | Enabled | [0] 5 minute low < 1300 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 39 | Enabled | [-1] 5 minute low > 1300 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 40 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 41 | Enabled | [0] 5 minute low < 1400 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 42 | Enabled | [-1] 5 minute low > 1400 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 43 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 44 | Enabled | [0] 5 minute low < 1500 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 45 | Enabled | [-1] 5 minute low > 1500 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 46 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 47 | Enabled | [0] 5 minute low < 1600 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 48 | Enabled | [-1] 5 minute low > 1600 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 49 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 50 | Enabled | [0] 5 minute low < 1700 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 51 | Enabled | [-1] 5 minute low > 1700 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 52 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 53 | Enabled | [0] 5 minute low < 1800 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 54 | Enabled | [-1] 5 minute low > 1800 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 55 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 56 | Enabled | [0] 5 minute low < 1900 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 57 | Enabled | [-1] 5 minute low > 1900 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 58 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 59 | Enabled | [0] 5 minute low < 2000 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 60 | Enabled | [-1] 5 minute low > 2000 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 61 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 62 | Enabled | [0] 5 minute low < 2100 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 63 | Enabled | [-1] 5 minute low > 2100 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 64 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 65 | Enabled | [0] 5 minute low < 2200 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 66 | Enabled | [-1] 5 minute low > 2200 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 67 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 68 | Enabled | [0] 5 minute low < 2300 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 69 | Enabled | [-1] 5 minute low > 2300 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 70 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 71 | Enabled | [0] 5 minute low < 2400 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 72 | Enabled | [-1] 5 minute low > 2400 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 73 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 74 | Enabled | [0] 5 minute low < 2500 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 75 | Enabled | [-1] 5 minute low > 2500 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 76 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 77 | Enabled | [0] 5 minute low < 2600 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 78 | Enabled | [-1] 5 minute low > 2600 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 79 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 80 | Enabled | [0] 5 minute low < 2700 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 81 | Enabled | [-1] 5 minute low > 2700 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 82 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 83 | Enabled | [0] 5 minute low < 2800 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 84 | Enabled | [-1] 5 minute low > 2800 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 85 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 86 | Enabled | [0] 5 minute low < 2900 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 87 | Enabled | [-1] 5 minute low > 2900 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 88 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 89 | Enabled | [0] 5 minute low < 3000 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 90 | Enabled | [-1] 5 minute low > 3000 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **60** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[0] 5 minute low < 100` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#3** `[-1] 5 minute low > 100` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[0] 5 minute low < 200` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[-1] 5 minute low > 200` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[0] 5 minute low < 300` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[-1] 5 minute low > 300` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#11** `[0] 5 minute low < 400` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#12** `[-1] 5 minute low > 400` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#14** `[0] 5 minute low < 500` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#15** `[-1] 5 minute low > 500` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#17** `[0] 5 minute low < 600` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#18** `[-1] 5 minute low > 600` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#20** `[0] 5 minute low < 700` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#21** `[-1] 5 minute low > 700` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#23** `[0] 5 minute low < 800` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#24** `[-1] 5 minute low > 800` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#26** `[0] 5 minute low < 900` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#27** `[-1] 5 minute low > 900` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#29** `[0] 5 minute low < 1000` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#30** `[-1] 5 minute low > 1000` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#32** `[0] 5 minute low < 1100` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#33** `[-1] 5 minute low > 1100` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#35** `[0] 5 minute low < 1200` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#36** `[-1] 5 minute low > 1200` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#38** `[0] 5 minute low < 1300` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#39** `[-1] 5 minute low > 1300` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#41** `[0] 5 minute low < 1400` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#42** `[-1] 5 minute low > 1400` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#44** `[0] 5 minute low < 1500` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#45** `[-1] 5 minute low > 1500` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#47** `[0] 5 minute low < 1600` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#48** `[-1] 5 minute low > 1600` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#50** `[0] 5 minute low < 1700` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#51** `[-1] 5 minute low > 1700` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#53** `[0] 5 minute low < 1800` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#54** `[-1] 5 minute low > 1800` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#56** `[0] 5 minute low < 1900` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#57** `[-1] 5 minute low > 1900` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#59** `[0] 5 minute low < 2000` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#60** `[-1] 5 minute low > 2000` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#62** `[0] 5 minute low < 2100` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#63** `[-1] 5 minute low > 2100` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#65** `[0] 5 minute low < 2200` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#66** `[-1] 5 minute low > 2200` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#68** `[0] 5 minute low < 2300` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#69** `[-1] 5 minute low > 2300` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#71** `[0] 5 minute low < 2400` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#72** `[-1] 5 minute low > 2400` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#74** `[0] 5 minute low < 2500` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#75** `[-1] 5 minute low > 2500` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#77** `[0] 5 minute low < 2600` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#78** `[-1] 5 minute low > 2600` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#80** `[0] 5 minute low < 2700` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#81** `[-1] 5 minute low > 2700` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#83** `[0] 5 minute low < 2800` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#84** `[-1] 5 minute low > 2800` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#86** `[0] 5 minute low < 2900` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#87** `[-1] 5 minute low > 2900` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#89** `[0] 5 minute low < 3000` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#90** `[-1] 5 minute low > 3000` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `low` — appears 60 time(s) in the expression tree

### Operators observed
- `<` — 30 occurrence(s)
- `>` — 30 occurrence(s)

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
- Timeframe tokens: `1_days_ago`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Other.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **60** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Other
- **Tags:** universe:futures, timeframe:intraday-bars
- **Root universe:** futures
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 9023427
scan_name: accdist jump
source_url: https://chartink.com/screener/accdist-jump
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Momentum"]
tags: ["universe:cash","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 9
disabled_filter_count: 10
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# accdist jump

## Source

- Chartink URL: https://chartink.com/screener/accdist-jump
- Scan ID: `9023427`
- Slug: `accdist-jump`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2022-07-14T06:35:19.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/9023427.json](../source-snapshots/9023427.json)
- Text snapshot: [source-snapshots/9023427.txt](../source-snapshots/9023427.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **9** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.

The active tests, in captured order:
- [0] 60 minute accdist - [-100] 60 minute accdist crossed above 20
- [0] 5 minute accdist1 crossed above [-1] 5 minute max( 2000 ,  [0] 5 minute accdist1 )
- [-50] 5 minute accdist1 < [-51] 5 minute max( 950 ,  [0] 5 minute accdist1 )
- [0] 30 minute accdist1 crossed above [-1] 30 minute max( 2000 ,  [0] 30 minute accdist1 )
- [0] 30 minute accdist1 crossed below [-1] 30 minute min( 2000 ,  [0] 30 minute accdist1 )
- [0] 60 minute accdist1 crossed above [-1] 60 minute max( 1000 ,  [0] 60 minute accdist1 )
- [0] 60 minute accdist1 crossed below [-1] 60 minute min( 1000 ,  [0] 60 minute accdist1 )
- daily accdist1 crossed above 1 day ago max( 1000 ,  daily accdist1 )
- daily accdist1 crossed below 1 day ago min( 1000 ,  daily accdist1 )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: accdist jump
Scan id: 9023427
Slug: accdist-jump
Source URL: https://chartink.com/screener/accdist-jump
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-07-14T06:35:19.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] 1 day ago close * 1 day ago volume > 100000000
2. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Disabled] [0] 60 minute accdist crossed above [-50] 60 minute accdist * 20
    group_path: root/group[cash|all]
4. [Disabled] ( [0] 60 minute accdist - [-50] 60 minute accdist ) * 100 / [-50] 60 minute accdist crossed above 2000
    group_path: root/group[cash|all]
5. [Enabled] [0] 60 minute accdist - [-100] 60 minute accdist crossed above 20
    group_path: root/group[cash|all]
6. [Disabled] ( [0] 60 minute accdist / 100000 ) - ( [-100] 60 minute accdist / 100000 ) > 0.01
    group_path: root/group[cash|all]
7. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Disabled] [0] 60 minute cmf( 200 ) - [-7] 60 minute cmf( 21 ) crossed above 0.5
    group_path: root/group[cash|all]
9. [Disabled] [0] 60 minute accdist1 - [0] 60 minute accdist1 crossed above 1000000
    group_path: root/group[cash|all]
10. [Disabled] [0] 60 minute accdist1 crossed above 10000000 + [-8] 60 minute accdist1
    group_path: root/group[cash|all]
11. [Disabled] [0] 5 minute accdist1 crossed above 10000000 + [-8] 5 minute accdist1
    group_path: root/group[cash|all]
12. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
13. [Enabled] [0] 5 minute accdist1 crossed above [-1] 5 minute max( 2000 ,  [0] 5 minute accdist1 )
    group_path: root/group[cash|all]
14. [Enabled] [-50] 5 minute accdist1 < [-51] 5 minute max( 950 ,  [0] 5 minute accdist1 )
    group_path: root/group[cash|all]
15. [Disabled] [0] 5 minute accdist1 crossed below [-1] 5 minute min( 1000 ,  [0] 5 minute accdist1 )
    group_path: root/group[cash|all]
16. [Disabled] [-50] 5 minute accdist1 > [-51] 5 minute min( 950 ,  [0] 5 minute accdist1 )
    group_path: root/group[cash|all]
17. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
18. [Enabled] [0] 30 minute accdist1 crossed above [-1] 30 minute max( 2000 ,  [0] 30 minute accdist1 )
    group_path: root/group[cash|any]
19. [Enabled] [0] 30 minute accdist1 crossed below [-1] 30 minute min( 2000 ,  [0] 30 minute accdist1 )
    group_path: root/group[cash|any]
20. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
21. [Enabled] [0] 60 minute accdist1 crossed above [-1] 60 minute max( 1000 ,  [0] 60 minute accdist1 )
    group_path: root/group[cash|any]
22. [Enabled] [0] 60 minute accdist1 crossed below [-1] 60 minute min( 1000 ,  [0] 60 minute accdist1 )
    group_path: root/group[cash|any]
23. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
24. [Enabled] daily accdist1 crossed above 1 day ago max( 1000 ,  daily accdist1 )
    group_path: root/group[cash|any]
25. [Enabled] daily accdist1 crossed below 1 day ago min( 1000 ,  daily accdist1 )
    group_path: root/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( [0] 30 minute "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" > [-1] 30 minute max( 2000 , [0] 30 minute "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) and [ -1 ] 30 minute "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" <= [ -2 ] 30 minute max( 2000 , [0] 30 minute "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) or [0] 30 minute "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" < [-1] 30 minute min( 2000 , [0] 30 minute "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) and [ -1 ] 30 minute "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" >= [ -2 ] 30 minute min( 2000 , [0] 30 minute "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) ) ) and( cash ( [0] 1 hour "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" > [-1] 1 hour max( 1000 , [0] 1 hour "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) and [ -1 ] 1 hour "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" <= [ -2 ] 1 hour max( 1000 , [0] 1 hour "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) or [0] 1 hour "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" < [-1] 1 hour min( 1000 , [0] 1 hour "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) and [ -1 ] 1 hour "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" >= [ -2 ] 1 hour min( 1000 , [0] 1 hour "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) ) ) and( cash ( latest "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" > 1 day ago max( 1000 , latest "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) and 1 day ago  "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" <= 2 day ago  max( 1000 , latest "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) or latest "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" < 1 day ago min( 1000 , latest "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) and 1 day ago  "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" >= 2 day ago  min( 1000 , latest "( ( 2 *  close -  low -  high ) / (  high -  low ) ) *  volume" ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |
| 2 | 3 | Disabled | root/group[cash\|all] | [0] 60 minute accdist crossed above [-50] 60 minute accdist * 20 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 4 | Disabled | root/group[cash\|all] | ( [0] 60 minute accdist - [-50] 60 minute accdist ) * 100 / [-50] 60 minute accdist crossed above 2000 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 5 | Enabled | root/group[cash\|all] | [0] 60 minute accdist - [-100] 60 minute accdist crossed above 20 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 6 | Disabled | root/group[cash\|all] | ( [0] 60 minute accdist / 100000 ) - ( [-100] 60 minute accdist / 100000 ) > 0.01 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 8 | Disabled | root/group[cash\|all] | [0] 60 minute cmf( 200 ) - [-7] 60 minute cmf( 21 ) crossed above 0.5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 9 | Disabled | root/group[cash\|all] | [0] 60 minute accdist1 - [0] 60 minute accdist1 crossed above 1000000 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 10 | Disabled | root/group[cash\|all] | [0] 60 minute accdist1 crossed above 10000000 + [-8] 60 minute accdist1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 11 | Disabled | root/group[cash\|all] | [0] 5 minute accdist1 crossed above 10000000 + [-8] 5 minute accdist1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 13 | Enabled | root/group[cash\|all] | [0] 5 minute accdist1 crossed above [-1] 5 minute max( 2000 ,  [0] 5 minute accdist1 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 14 | Enabled | root/group[cash\|all] | [-50] 5 minute accdist1 < [-51] 5 minute max( 950 ,  [0] 5 minute accdist1 ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 15 | Disabled | root/group[cash\|all] | [0] 5 minute accdist1 crossed below [-1] 5 minute min( 1000 ,  [0] 5 minute accdist1 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 16 | Disabled | root/group[cash\|all] | [-50] 5 minute accdist1 > [-51] 5 minute min( 950 ,  [0] 5 minute accdist1 ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 18 | Enabled | root/group[cash\|any] | [0] 30 minute accdist1 crossed above [-1] 30 minute max( 2000 ,  [0] 30 minute accdist1 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 19 | Enabled | root/group[cash\|any] | [0] 30 minute accdist1 crossed below [-1] 30 minute min( 2000 ,  [0] 30 minute accdist1 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | 21 | Enabled | root/group[cash\|any] | [0] 60 minute accdist1 crossed above [-1] 60 minute max( 1000 ,  [0] 60 minute accdist1 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 17 | 22 | Enabled | root/group[cash\|any] | [0] 60 minute accdist1 crossed below [-1] 60 minute min( 1000 ,  [0] 60 minute accdist1 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 18 | 24 | Enabled | root/group[cash\|any] | daily accdist1 crossed above 1 day ago max( 1000 ,  daily accdist1 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. |
| 19 | 25 | Enabled | root/group[cash\|any] | daily accdist1 crossed below 1 day ago min( 1000 ,  daily accdist1 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **9** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#5** `[0] 60 minute accdist - [-100] 60 minute accdist crossed above 20` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#13** `[0] 5 minute accdist1 crossed above [-1] 5 minute max( 2000 ,  [0] 5 minute accdist1 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#14** `[-50] 5 minute accdist1 < [-51] 5 minute max( 950 ,  [0] 5 minute accdist1 )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#18** `[0] 30 minute accdist1 crossed above [-1] 30 minute max( 2000 ,  [0] 30 minute accdist1 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#19** `[0] 30 minute accdist1 crossed below [-1] 30 minute min( 2000 ,  [0] 30 minute accdist1 )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#21** `[0] 60 minute accdist1 crossed above [-1] 60 minute max( 1000 ,  [0] 60 minute accdist1 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#22** `[0] 60 minute accdist1 crossed below [-1] 60 minute min( 1000 ,  [0] 60 minute accdist1 )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#24** `daily accdist1 crossed above 1 day ago max( 1000 ,  daily accdist1 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars.
- **#25** `daily accdist1 crossed below 1 day ago min( 1000 ,  daily accdist1 )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **10** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `1 day ago close * 1 day ago volume > 100000000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `[0] 60 minute accdist crossed above [-50] 60 minute accdist * 20`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `( [0] 60 minute accdist - [-50] 60 minute accdist ) * 100 / [-50] 60 minute accdist crossed above 2000`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `( [0] 60 minute accdist / 100000 ) - ( [-100] 60 minute accdist / 100000 ) > 0.01`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #8
- **Condition (verbatim):** `[0] 60 minute cmf( 200 ) - [-7] 60 minute cmf( 21 ) crossed above 0.5`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `[0] 60 minute accdist1 - [0] 60 minute accdist1 crossed above 1000000`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #10
- **Condition (verbatim):** `[0] 60 minute accdist1 crossed above 10000000 + [-8] 60 minute accdist1`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `[0] 5 minute accdist1 crossed above 10000000 + [-8] 5 minute accdist1`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #15
- **Condition (verbatim):** `[0] 5 minute accdist1 crossed below [-1] 5 minute min( 1000 ,  [0] 5 minute accdist1 )`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `[-50] 5 minute accdist1 > [-51] 5 minute min( 950 ,  [0] 5 minute accdist1 )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `custom_indicator_56921` — appears 26 time(s) in the expression tree
- `accdist` — appears 9 time(s) in the expression tree
- `max` — appears 5 time(s) in the expression tree
- `min` — appears 5 time(s) in the expression tree
- `cmf` — appears 2 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 11 occurrence(s)
- `-` — 4 occurrence(s)
- `crossed below` — 4 occurrence(s)
- `*` — 3 occurrence(s)
- `>` — 3 occurrence(s)
- `+` — 2 occurrence(s)
- `/` — 1 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `21_days_ago`, `30_minute`, `5_minute`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **9** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **10** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Momentum
- **Tags:** universe:cash, timeframe:intraday-bars, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

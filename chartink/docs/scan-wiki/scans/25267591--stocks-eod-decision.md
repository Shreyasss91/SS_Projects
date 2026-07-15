---
scan_id: 25267591
scan_name: stocks eod decision
source_url: https://chartink.com/screener/top-gainer-4-2
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volatility", "Volume/delivery", "Multi-factor"]
tags: ["universe:nifty-200", "indicator:volume", "indicator:sma", "timeframe:intraday-bars", "timeframe:weekly", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 11
disabled_filter_count: 4
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# stocks eod decision

## Source

- Chartink URL: https://chartink.com/screener/top-gainer-4-2
- Scan ID: `25267591`
- Slug: `top-gainer-4-2`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2026-02-06T08:41:45.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/25267591.json](../source-snapshots/25267591.json)
- Text snapshot: [source-snapshots/25267591.txt](../source-snapshots/25267591.txt)

## What this scan is for

This scan, titled "stocks eod decision", appears designed to screen Indian equities in the **nifty 200** universe using **11 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Moving average, Volatility, Volume/delivery, Multi-factor**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 120_minute, 15_minute, 1_days_ago, 1_weeks_ago, 60_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: stocks eod decision
Scan id: 25267591
Slug: top-gainer-4-2
Source URL: https://chartink.com/screener/top-gainer-4-2
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2026-02-06T08:41:45.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
2. [Disabled] daily % change > 4
    group_path: root/group[cash|any]
3. [Enabled] daily % change < -4
    group_path: root/group[cash|any]
4. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Disabled] daily volume > daily sma( close ,  20 ) * 3
    group_path: root/group[cash|all]
6. [Enabled] [0] 15 minute volume > [0] 15 minute sma( close ,  30 ) * 6
    group_path: root/group[cash|all]
7. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Enabled] ( daily abs( daily open - daily close ) ) < 1 day ago min( 5 ,  daily abs( daily open - daily close ) ) * 0.2
    group_path: root/group[cash|all]
9. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
10. [Enabled] daily avg true range( 1 ) > 1 day ago avg true range( 14 ) * 3
    group_path: root/group[cash|all]
11. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
12. [Enabled] [1] 120 minute % change < -2
    group_path: root/group[cash|any]
13. [Enabled] [1] 120 minute % change > 2
    group_path: root/group[cash|any]
14. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
15. [Enabled] daily close * daily volume > 1 day ago sma( close ,  20 ) * 2
    group_path: root/group[cash|all]
16. [Disabled] daily buyer initiated trades ratio > 2
    group_path: root/group[cash|all]
17. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
18. [Disabled] ( daily high - [0] 60 minute low ) / daily high > 0.035
    group_path: root/group[cash|all]
19. [Enabled] ( 1 day ago high - [0] 60 minute low ) / 1 day ago high > 0.05
    group_path: root/group[cash|all]
20. [Disabled] [GROUP segment=cash join=any_2 combination=passes measurevalue=default]  (path: root/group[cash|any_2])
21. [Enabled] 1.005 > daily greatest / daily least
    group_path: root/group[cash|any_2]
22. [Enabled] 1.005 > daily greatest / daily least
    group_path: root/group[cash|any_2]
23. [Enabled] 1.005 > daily greatest / daily least
    group_path: root/group[cash|any_2]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( ( cash (  (  1 day ago high -  [0] 1 hour low ) /  1 day ago high >  0.05 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [GROUP segment=cash join=any combination=passes measurevalue=default] | Nested group over segment **cash** with join **any** (combination=passes). Group status=Disabled. |
| 2 | Disabled | daily % change > 4 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 3 | Enabled | daily % change < -4 | Inequality test: left expression must be strictly less than right. |
| 4 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 5 | Disabled | daily volume > daily sma( close ,  20 ) * 3 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 6 | Enabled | [0] 15 minute volume > [0] 15 minute sma( close ,  30 ) * 6 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 8 | Enabled | ( daily abs( daily open - daily close ) ) < 1 day ago min( 5 ,  daily abs( daily open - daily close ) ) * 0.2 | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |
| 9 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 10 | Enabled | daily avg true range( 1 ) > 1 day ago avg true range( 14 ) * 3 | Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. |
| 11 | Disabled | [GROUP segment=cash join=any combination=passes measurevalue=default] | Nested group over segment **cash** with join **any** (combination=passes). Group status=Disabled. |
| 12 | Enabled | [1] 120 minute % change < -2 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | Enabled | [1] 120 minute % change > 2 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 15 | Enabled | daily close * daily volume > 1 day ago sma( close ,  20 ) * 2 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 16 | Disabled | daily buyer initiated trades ratio > 2 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 17 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 18 | Disabled | ( daily high - [0] 60 minute low ) / daily high > 0.035 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 19 | Enabled | ( 1 day ago high - [0] 60 minute low ) / 1 day ago high > 0.05 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 20 | Disabled | [GROUP segment=cash join=any_2 combination=passes measurevalue=default] | Nested group over segment **cash** with join **any_2** (combination=passes). Group status=Disabled. |
| 21 | Enabled | 1.005 > daily greatest / daily least | Inequality test: left expression must be strictly greater than right. |
| 22 | Enabled | 1.005 > daily greatest / daily least | Inequality test: left expression must be strictly greater than right. |
| 23 | Enabled | 1.005 > daily greatest / daily least | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **11** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `daily % change < -4` — Inequality test: left expression must be strictly less than right.
- **#6** `[0] 15 minute volume > [0] 15 minute sma( close ,  30 ) * 6` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `( daily abs( daily open - daily close ) ) < 1 day ago min( 5 ,  daily abs( daily open - daily close ) ) * 0.2` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.
- **#10** `daily avg true range( 1 ) > 1 day ago avg true range( 14 ) * 3` — Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction.
- **#12** `[1] 120 minute % change < -2` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#13** `[1] 120 minute % change > 2` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#15** `daily close * daily volume > 1 day ago sma( close ,  20 ) * 2` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#19** `( 1 day ago high - [0] 60 minute low ) / 1 day ago high > 0.05` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#21** `1.005 > daily greatest / daily least` — Inequality test: left expression must be strictly greater than right.
- **#22** `1.005 > daily greatest / daily least` — Inequality test: left expression must be strictly greater than right.
- **#23** `1.005 > daily greatest / daily least` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **4** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #2
- **Condition (verbatim):** `daily % change > 4`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily volume > daily sma( close ,  20 ) * 3`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `daily buyer initiated trades ratio > 2`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #18
- **Condition (verbatim):** `( daily high - [0] 60 minute low ) / daily high > 0.035`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `high` — appears 14 time(s) in the expression tree
- `low` — appears 12 time(s) in the expression tree
- `close` — appears 10 time(s) in the expression tree
- `volume` — appears 6 time(s) in the expression tree
- `% change` — appears 4 time(s) in the expression tree
- `sma` — appears 3 time(s) in the expression tree
- `greatest` — appears 3 time(s) in the expression tree
- `least` — appears 3 time(s) in the expression tree
- `abs` — appears 2 time(s) in the expression tree
- `open` — appears 2 time(s) in the expression tree
- `avg true range` — appears 2 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree
- `buyer initiated trades ratio` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 12 occurrence(s)
- `/` — 11 occurrence(s)
- `*` — 6 occurrence(s)
- `<` — 3 occurrence(s)
- `+` — 2 occurrence(s)
- `-` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `120_minute`, `15_minute`, `1_days_ago`, `1_weeks_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volatility, Volume/delivery, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **11** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **4** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Moving average, Volatility, Volume/delivery, Multi-factor
- **Tags:** universe:nifty-200, indicator:volume, indicator:sma, timeframe:intraday-bars, timeframe:weekly, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

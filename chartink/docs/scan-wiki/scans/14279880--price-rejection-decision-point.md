---
scan_id: 14279880
scan_name: price rejection+ decision point
source_url: https://chartink.com/screener/price-rejection-decision-point
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volatility", "Volume/delivery", "Trend following", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-200", "indicator:atr", "indicator:volume", "indicator:sma", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 14
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# price rejection+ decision point

## Source

- Chartink URL: https://chartink.com/screener/price-rejection-decision-point
- Scan ID: `14279880`
- Slug: `price-rejection-decision-point`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-12-20T02:42:11.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14279880.json](../source-snapshots/14279880.json)
- Text snapshot: [source-snapshots/14279880.txt](../source-snapshots/14279880.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **14** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average, Volatility, Volume/delivery, Trend following, Momentum, Multi-factor**.
The active tests, in captured order, are:
- daily count( 5, 1 where ( daily least - daily low ) / ( daily high - daily low ) > 0.5 ) >= 1
- daily count( 5, 1 where daily open > 1 day ago close * 1.01 ) >= 1
- daily count( 5, 1 where daily volume > 1 day ago volume * 2 ) >= 1
- ( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3
- daily abs( ( [0] 15 minute close / 1 day ago close ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 2 days ago close ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 3 days ago close ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 4 days ago close ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 5 days ago close ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 1 day ago low ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 2 days ago low ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 3 days ago low ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 4 days ago low ) - 1 ) crossed below 0.005
- daily abs( ( [0] 15 minute close / 5 days ago low ) - 1 ) crossed below 0.005

Author description (source metadata): if price rejection has happened at previous gaps, S/R...it is good bullish signal.

price rejection from bottom has happened in previuos couple of days,
bullish gap ups also seen in previuos couple of days,
Volume interest is also in one or more days in previuos couple of days.

So for these bullish stocks when price comes near previous days decision points like Low, close etc,.
its a good oppurtunity to buy intraday or positional trade

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: price rejection+ decision point
Scan id: 14279880
Slug: price-rejection-decision-point
Source URL: https://chartink.com/screener/price-rejection-decision-point
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-20T02:42:11.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily count( 5, 1 where ( daily least - daily low ) / ( daily high - daily low ) > 0.5 ) >= 1
2. [Enabled] daily count( 5, 1 where daily open > 1 day ago close * 1.01 ) >= 1
3. [Enabled] daily count( 5, 1 where daily volume > 1 day ago volume * 2 ) >= 1
4. [Enabled] ( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3
5. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
6. [Enabled] daily abs( ( [0] 15 minute close / 1 day ago close ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
7. [Enabled] daily abs( ( [0] 15 minute close / 2 days ago close ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
8. [Enabled] daily abs( ( [0] 15 minute close / 3 days ago close ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
9. [Enabled] daily abs( ( [0] 15 minute close / 4 days ago close ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
10. [Enabled] daily abs( ( [0] 15 minute close / 5 days ago close ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
11. [Enabled] daily abs( ( [0] 15 minute close / 1 day ago low ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
12. [Enabled] daily abs( ( [0] 15 minute close / 2 days ago low ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
13. [Enabled] daily abs( ( [0] 15 minute close / 3 days ago low ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
14. [Enabled] daily abs( ( [0] 15 minute close / 4 days ago low ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]
15. [Enabled] daily abs( ( [0] 15 minute close / 5 days ago low ) - 1 ) crossed below 0.005
    group_path: root/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( latest count( 5, 1 where( least(  latest open, latest close  ) - latest low ) / ( latest high - latest low ) > 0.5 ) >= 1 and latest count( 5, 1 where latest open > 1 day ago close * 1.01 ) >= 1 and latest count( 5, 1 where latest volume > 1 day ago volume * 2 ) >= 1 and( latest avg true range( 7 ) / latest sma( latest close , 7 ) ) * 100 > 3 and( cash ( abs( ( [0] 15 minute close / 1 day ago close ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 2 day ago  close ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 2 days ago close ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 3 days ago  close ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 3 days ago close ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 4 days ago  close ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 4 days ago close ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 5 days ago  close ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 5 days ago close ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 6 days ago  close ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 1 day ago low ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 2 day ago  low ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 2 days ago low ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 3 days ago  low ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 3 days ago low ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 4 days ago  low ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 4 days ago low ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 5 days ago  low ) - 1 ) >= 0.005 or abs( ( [0] 15 minute close / 5 days ago low ) - 1 ) < 0.005 and abs( ( [ -1 ] 15 minute close / 6 days ago  low ) - 1 ) >= 0.005 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily count( 5, 1 where ( daily least - daily low ) / ( daily high - daily low ) > 0.5 ) >= 1 | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | daily count( 5, 1 where daily open > 1 day ago close * 1.01 ) >= 1 | Inequality test: left expression must be strictly greater than right. |
| 3 | 3 | Enabled | root | daily count( 5, 1 where daily volume > 1 day ago volume * 2 ) >= 1 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 4 | 4 | Enabled | root | ( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. ATR measures smoothed true range (volatility), not direction. |
| 5 | 6 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 1 day ago close ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 7 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 2 days ago close ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 8 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 3 days ago close ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 9 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 4 days ago close ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 10 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 5 days ago close ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 11 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 1 day ago low ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 12 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 2 days ago low ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 13 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 3 days ago low ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 14 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 4 days ago low ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 15 | Enabled | root/group[cash\|any] | daily abs( ( [0] 15 minute close / 5 days ago low ) - 1 ) crossed below 0.005 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **14** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily count( 5, 1 where ( daily least - daily low ) / ( daily high - daily low ) > 0.5 ) >= 1` — Inequality test: left expression must be strictly greater than right.
- **#2** `daily count( 5, 1 where daily open > 1 day ago close * 1.01 ) >= 1` — Inequality test: left expression must be strictly greater than right.
- **#3** `daily count( 5, 1 where daily volume > 1 day ago volume * 2 ) >= 1` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#4** `( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. ATR measures smoothed true range (volatility), not direction.
- **#6** `daily abs( ( [0] 15 minute close / 1 day ago close ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `daily abs( ( [0] 15 minute close / 2 days ago close ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `daily abs( ( [0] 15 minute close / 3 days ago close ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `daily abs( ( [0] 15 minute close / 4 days ago close ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `daily abs( ( [0] 15 minute close / 5 days ago close ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#11** `daily abs( ( [0] 15 minute close / 1 day ago low ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#12** `daily abs( ( [0] 15 minute close / 2 days ago low ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#13** `daily abs( ( [0] 15 minute close / 3 days ago low ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#14** `daily abs( ( [0] 15 minute close / 4 days ago low ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#15** `daily abs( ( [0] 15 minute close / 5 days ago low ) - 1 ) crossed below 0.005` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 18 time(s) in the expression tree
- `abs` — appears 10 time(s) in the expression tree
- `low` — appears 7 time(s) in the expression tree
- `count` — appears 3 time(s) in the expression tree
- `open` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `least` — appears 1 time(s) in the expression tree
- `avg true range` — appears 1 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed below` — 10 occurrence(s)
- `>` — 4 occurrence(s)
- `>=` — 3 occurrence(s)
- `*` — 3 occurrence(s)
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
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_days_ago`, `2_days_ago`, `3_days_ago`, `4_days_ago`, `5_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volatility, Volume/delivery, Trend following, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **14** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Moving average, Volatility, Volume/delivery, Trend following, Momentum, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-200, indicator:atr, indicator:volume, indicator:sma, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

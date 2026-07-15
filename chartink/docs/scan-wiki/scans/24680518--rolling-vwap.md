---
scan_id: 24680518
scan_name: Rolling VWAP
source_url: https://chartink.com/screener/rolling-vwap-2
market: Indian equities
horizon: Swing
classification: ["Moving average", "Volume/delivery", "Trend following", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "universe:nifty-200", "indicator:vwap", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# Rolling VWAP

## Source

- Chartink URL: https://chartink.com/screener/rolling-vwap-2
- Scan ID: `24680518`
- Slug: `rolling-vwap-2`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2025-12-04T07:42:44.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24680518.json](../source-snapshots/24680518.json)
- Text snapshot: [source-snapshots/24680518.txt](../source-snapshots/24680518.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **8** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Trend following, Momentum, Multi-factor**.
The active tests, in captured order, are:
- daily count( 30, 1 where daily low crossed above daily sma( close ,  89 ) ) >= 1
- daily count( 30, 1 where daily low crossed above daily sma( close ,  144 ) ) >= 1
- daily count( 30, 1 where daily low crossed above daily sma( close ,  233 ) ) >= 1
- daily count( 30, 1 where daily low crossed above daily sma( close ,  377 ) ) >= 1
- daily count( 30, 1 where daily low crossed above daily sma( close ,  89 ) ) crossed above 0
- daily count( 30, 1 where daily low crossed above daily sma( close ,  144 ) ) crossed above 0
- daily count( 30, 1 where daily low crossed above daily sma( close ,  233 ) ) crossed above 0
- daily count( 30, 1 where daily low crossed above daily sma( close ,  377 ) ) crossed above 0

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Rolling VWAP
Scan id: 24680518
Slug: rolling-vwap-2
Source URL: https://chartink.com/screener/rolling-vwap-2
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-12-04T07:42:44.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily count( 30, 1 where daily low crossed above daily sma( close ,  89 ) ) >= 1
    group_path: root/group[cash|all]
3. [Enabled] daily count( 30, 1 where daily low crossed above daily sma( close ,  144 ) ) >= 1
    group_path: root/group[cash|all]
4. [Enabled] daily count( 30, 1 where daily low crossed above daily sma( close ,  233 ) ) >= 1
    group_path: root/group[cash|all]
5. [Enabled] daily count( 30, 1 where daily low crossed above daily sma( close ,  377 ) ) >= 1
    group_path: root/group[cash|all]
6. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any])
7. [Enabled] daily count( 30, 1 where daily low crossed above daily sma( close ,  89 ) ) crossed above 0
    group_path: root/group[cash|all]/group[cash|any]
8. [Enabled] daily count( 30, 1 where daily low crossed above daily sma( close ,  144 ) ) crossed above 0
    group_path: root/group[cash|all]/group[cash|any]
9. [Enabled] daily count( 30, 1 where daily low crossed above daily sma( close ,  233 ) ) crossed above 0
    group_path: root/group[cash|all]/group[cash|any]
10. [Enabled] daily count( 30, 1 where daily low crossed above daily sma( close ,  377 ) ) crossed above 0
    group_path: root/group[cash|all]/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( daily count( 30, 1 where daily low > daily sma( daily vwap , 89 ) and 1 day ago  low <= 1 day ago  sma( daily vwap , 89 ) ) >= 1 and daily count( 30, 1 where daily low > daily sma( daily vwap , 144 ) and 1 day ago  low <= 1 day ago  sma( daily vwap , 144 ) ) >= 1 and daily count( 30, 1 where daily low > daily sma( daily vwap , 233 ) and 1 day ago  low <= 1 day ago  sma( daily vwap , 233 ) ) >= 1 and daily count( 30, 1 where daily low > daily sma( daily vwap , 377 ) and 1 day ago  low <= 1 day ago  sma( daily vwap , 377 ) ) >= 1 and( cash ( daily count( 30, 1 where daily low > daily sma( daily vwap , 89 ) and 1 day ago  low <= 1 day ago  sma( daily vwap , 89 ) ) > 0 and 1 day ago  count( 30, 1 where daily low > 1 day ago  sma( daily vwap , 89 )and 1 day ago  low <= 2 day ago   sma( daily vwap , 89 )) <= 0 or daily count( 30, 1 where daily low > daily sma( daily vwap , 144 ) and 1 day ago  low <= 1 day ago  sma( daily vwap , 144 ) ) > 0 and 1 day ago  count( 30, 1 where daily low > 1 day ago  sma( daily vwap , 144 )and 1 day ago  low <= 2 day ago   sma( daily vwap , 144 )) <= 0 or daily count( 30, 1 where daily low > daily sma( daily vwap , 233 ) and 1 day ago  low <= 1 day ago  sma( daily vwap , 233 ) ) > 0 and 1 day ago  count( 30, 1 where daily low > 1 day ago  sma( daily vwap , 233 )and 1 day ago  low <= 2 day ago   sma( daily vwap , 233 )) <= 0 or daily count( 30, 1 where daily low > daily sma( daily vwap , 377 ) and 1 day ago  low <= 1 day ago  sma( daily vwap , 377 ) ) > 0 and 1 day ago  count( 30, 1 where daily low > 1 day ago  sma( daily vwap , 377 )and 1 day ago  low <= 2 day ago   sma( daily vwap , 377 )) <= 0 ) ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily count( 30, 1 where daily low crossed above daily sma( close ,  89 ) ) >= 1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily count( 30, 1 where daily low crossed above daily sma( close ,  144 ) ) >= 1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily count( 30, 1 where daily low crossed above daily sma( close ,  233 ) ) >= 1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 4 | 5 | Enabled | root/group[cash\|all] | daily count( 30, 1 where daily low crossed above daily sma( close ,  377 ) ) >= 1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 5 | 7 | Enabled | root/group[cash\|all]/group[cash\|any] | daily count( 30, 1 where daily low crossed above daily sma( close ,  89 ) ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 6 | 8 | Enabled | root/group[cash\|all]/group[cash\|any] | daily count( 30, 1 where daily low crossed above daily sma( close ,  144 ) ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 7 | 9 | Enabled | root/group[cash\|all]/group[cash\|any] | daily count( 30, 1 where daily low crossed above daily sma( close ,  233 ) ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |
| 8 | 10 | Enabled | root/group[cash\|all]/group[cash\|any] | daily count( 30, 1 where daily low crossed above daily sma( close ,  377 ) ) crossed above 0 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily count( 30, 1 where daily low crossed above daily sma( close ,  89 ) ) >= 1` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#3** `daily count( 30, 1 where daily low crossed above daily sma( close ,  144 ) ) >= 1` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#4** `daily count( 30, 1 where daily low crossed above daily sma( close ,  233 ) ) >= 1` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#5** `daily count( 30, 1 where daily low crossed above daily sma( close ,  377 ) ) >= 1` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#7** `daily count( 30, 1 where daily low crossed above daily sma( close ,  89 ) ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#8** `daily count( 30, 1 where daily low crossed above daily sma( close ,  144 ) ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#9** `daily count( 30, 1 where daily low crossed above daily sma( close ,  233 ) ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.
- **#10** `daily count( 30, 1 where daily low crossed above daily sma( close ,  377 ) ) crossed above 0` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars.

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
- `count` — appears 8 time(s) in the expression tree
- `low` — appears 8 time(s) in the expression tree
- `sma` — appears 8 time(s) in the expression tree
- `vwap` — appears 8 time(s) in the expression tree

### Operators observed
- `crossed above` — 12 occurrence(s)
- `>=` — 4 occurrence(s)

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
- Timeframe tokens: `0_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery, Trend following, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average, Volume/delivery, Trend following, Momentum, Multi-factor
- **Tags:** bias:upward-condition, universe:nifty-200, indicator:vwap, indicator:sma, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

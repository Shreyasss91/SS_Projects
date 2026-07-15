---
scan_id: 7333566
scan_name: cumulative volume _ Accumalation
source_url: https://chartink.com/screener/cumulative-volume-accumalation
market: Indian equities
horizon: "Intraday"
classification: ["Moving average","Volume/delivery","Momentum"]
tags: ["universe:cash","indicator:sma","indicator:volume","timeframe:intraday-bars","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Moving average
---

# cumulative volume _ Accumalation

## Source

- Chartink URL: https://chartink.com/screener/cumulative-volume-accumalation
- Scan ID: `7333566`
- Slug: `cumulative-volume-accumalation`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2022-01-01T08:19:17.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/7333566.json](../source-snapshots/7333566.json)
- Text snapshot: [source-snapshots/7333566.txt](../source-snapshots/7333566.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **5** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Momentum**.

The active tests, in captured order:
- [0] 60 minute sum( close ,  200 ) crossed above [0] 60 minute sma( close ,  100 )
- ( daily close * daily max( 100 ,  daily volume ) ) < 1 day ago min( 100 ,  daily close * daily max( 100 ,  daily volume ) ) * 1.01
- ( daily close * daily max( 100 ,  daily volume ) ) > 1 day ago min( 100 ,  daily close * daily max( 100 ,  daily volume ) ) * 0.99
- daily close crossed above 1 day ago min( 200 ,  daily low ) * 1.05
- [0] 60 minute close crossed below [-350] 60 minute min( 1500 ,  [0] 60 minute close )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: cumulative volume _ Accumalation
Scan id: 7333566
Slug: cumulative-volume-accumalation
Source URL: https://chartink.com/screener/cumulative-volume-accumalation
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-01-01T08:19:17.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] [0] 60 minute sum( close ,  200 ) crossed above [0] 60 minute sma( close ,  100 )
    group_path: root/group[cash|all]
3. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
4. [Enabled] ( daily close * daily max( 100 ,  daily volume ) ) < 1 day ago min( 100 ,  daily close * daily max( 100 ,  daily volume ) ) * 1.01
    group_path: root/group[cash|all]
5. [Enabled] ( daily close * daily max( 100 ,  daily volume ) ) > 1 day ago min( 100 ,  daily close * daily max( 100 ,  daily volume ) ) * 0.99
    group_path: root/group[cash|all]
6. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Enabled] daily close crossed above 1 day ago min( 200 ,  daily low ) * 1.05
    group_path: root/group[cash|all]
8. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
9. [Enabled] [0] 60 minute close crossed below [-350] 60 minute min( 1500 ,  [0] 60 minute close )
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( [0] 1 hour close < [-350] 1 hour min( 1500 , [0] 1 hour close ) and [ -1 ] 1 hour close >= [ -351 ] 1 hour min( 1500 , [0] 1 hour close ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | [0] 60 minute sum( close ,  200 ) crossed above [0] 60 minute sma( close ,  100 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 4 | Enabled | root/group[cash\|all] | ( daily close * daily max( 100 ,  daily volume ) ) < 1 day ago min( 100 ,  daily close * daily max( 100 ,  daily volume ) ) * 1.01 | Inequality test: left expression must be strictly less than right. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 3 | 5 | Enabled | root/group[cash\|all] | ( daily close * daily max( 100 ,  daily volume ) ) > 1 day ago min( 100 ,  daily close * daily max( 100 ,  daily volume ) ) * 0.99 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 4 | 7 | Enabled | root/group[cash\|all] | daily close crossed above 1 day ago min( 200 ,  daily low ) * 1.05 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 5 | 9 | Enabled | root/group[cash\|all] | [0] 60 minute close crossed below [-350] 60 minute min( 1500 ,  [0] 60 minute close ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[0] 60 minute sum( close ,  200 ) crossed above [0] 60 minute sma( close ,  100 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `( daily close * daily max( 100 ,  daily volume ) ) < 1 day ago min( 100 ,  daily close * daily max( 100 ,  daily volume ) ) * 1.01` — Inequality test: left expression must be strictly less than right. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#5** `( daily close * daily max( 100 ,  daily volume ) ) > 1 day ago min( 100 ,  daily close * daily max( 100 ,  daily volume ) ) * 0.99` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#7** `daily close crossed above 1 day ago min( 200 ,  daily low ) * 1.05` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#9** `[0] 60 minute close crossed below [-350] 60 minute min( 1500 ,  [0] 60 minute close )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `close` — appears 7 time(s) in the expression tree
- `volume` — appears 6 time(s) in the expression tree
- `min` — appears 4 time(s) in the expression tree
- `max` — appears 4 time(s) in the expression tree
- `sum` — appears 2 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree

### Operators observed
- `*` — 3 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `<` — 1 occurrence(s)
- `>` — 1 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Moving average, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **5** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
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
- **Methods:** Moving average, Volume/delivery, Momentum
- **Tags:** universe:cash, indicator:sma, indicator:volume, timeframe:intraday-bars, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

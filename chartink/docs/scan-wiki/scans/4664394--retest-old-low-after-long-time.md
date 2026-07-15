---
scan_id: 4664394
scan_name: Retest old low after long time
source_url: https://chartink.com/screener/retest-old-low-after-long-time
market: Indian equities
horizon: "Intraday"
classification: ["Volume/delivery","Momentum"]
tags: ["universe:cash","indicator:volume","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 12
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# Retest old low after long time

## Source

- Chartink URL: https://chartink.com/screener/retest-old-low-after-long-time
- Scan ID: `4664394`
- Slug: `retest-old-low-after-long-time`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-05-24T15:49:30.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4664394.json](../source-snapshots/4664394.json)
- Text snapshot: [source-snapshots/4664394.txt](../source-snapshots/4664394.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **12** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.

The active tests, in captured order:
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

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Retest old low after long time
Scan id: 4664394
Slug: retest-old-low-after-long-time
Source URL: https://chartink.com/screener/retest-old-low-after-long-time
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-05-24T15:49:30.000000Z

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

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 15 minute low < [-1] 15 minute min( 500 , [0] 15 minute low ) * 1.01 and [ -1 ] 15 minute low >= [ -2 ] 15 minute min( 500 , [0] 15 minute low )* 1.01 and [-1] 15 minute min( 499 , [0] 15 minute low ) < [-500] 15 minute min( 500 , [0] 15 minute low ) ) ) ) )
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

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **12** enabled leaf conditions. Disabled conditions are ignored at runtime.

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
- `low` — appears 16 time(s) in the expression tree
- `min` — appears 12 time(s) in the expression tree
- `close` — appears 4 time(s) in the expression tree
- `volume` — appears 4 time(s) in the expression tree

### Operators observed
- `*` — 5 occurrence(s)
- `>` — 4 occurrence(s)
- `crossed below` — 4 occurrence(s)
- `<` — 4 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `15_minute`, `1_days_ago`, `20_days_ago`, `21_days_ago`, `500_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Mean reversion, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **12** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Stretch conditions can highlight exhaustion zones inside ranges when broader trend is not strongly opposed.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Mean-reversion style thresholds can **fight strong trends** and produce repeated losers in momentum markets.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Momentum
- **Tags:** universe:cash, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

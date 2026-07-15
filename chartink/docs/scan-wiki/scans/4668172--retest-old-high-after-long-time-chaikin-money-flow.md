---
scan_id: 4668172
scan_name: Retest old high after long time Chaikin Money  Flow
source_url: https://chartink.com/screener/retest-old-high-after-long-time-chaikin-money-flow
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery","Breakout","Momentum"]
tags: ["universe:cash","indicator:volume","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: any
primary_classification: Volume/delivery
---

# Retest old high after long time Chaikin Money  Flow

## Source

- Chartink URL: https://chartink.com/screener/retest-old-high-after-long-time-chaikin-money-flow
- Scan ID: `4668172`
- Slug: `retest-old-high-after-long-time-chaikin-money-flow`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2021-05-25T01:58:51.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4668172.json](../source-snapshots/4668172.json)
- Text snapshot: [source-snapshots/4668172.txt](../source-snapshots/4668172.txt)

## What this scan is for

This is a **swing** screen over **cash** with **8** active leaf condition(s) under root join **any**.
Its method labels are derived only from active expressions: **Volume/delivery, Breakout, Momentum**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
- daily high crossed above 20 days ago max( 480 ,  daily high )
- 20 days ago max( 480 ,  daily high ) < 500 days ago max( 500 ,  daily high )
- 1 day ago close * 1 day ago volume > 100000000
- daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
- daily cmf( 21 ) crossed above 1 day ago max( 499 ,  daily cmf( 21 ) )
- 1 day ago max( 499 ,  daily cmf( 21 ) ) < 500 days ago max( 500 ,  daily cmf( 21 ) )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Retest old high after long time Chaikin Money  Flow
Scan id: 4668172
Slug: retest-old-high-after-long-time-chaikin-money-flow
Source URL: https://chartink.com/screener/retest-old-high-after-long-time-chaikin-money-flow
Root universe/segment: cash
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-05-25T01:58:51.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
    group_path: root/group[cash|all]
4. [Enabled] daily high crossed above 20 days ago max( 480 ,  daily high )
    group_path: root/group[cash|all]
5. [Enabled] 20 days ago max( 480 ,  daily high ) < 500 days ago max( 500 ,  daily high )
    group_path: root/group[cash|all]
6. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
8. [Enabled] daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
    group_path: root/group[cash|all]
9. [Enabled] daily cmf( 21 ) crossed above 1 day ago max( 499 ,  daily cmf( 21 ) )
    group_path: root/group[cash|all]
10. [Enabled] 1 day ago max( 499 ,  daily cmf( 21 ) ) < 500 days ago max( 500 ,  daily cmf( 21 ) )
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and latest count( 200, 1 where( latest high / latest low ) = 1 ) < 1 and latest high > 20 days ago max( 480 , latest high ) and 1 day ago  high <= 21 days ago  max( 480 , latest high ) and 20 days ago max( 480 , latest high ) < 500 days ago max( 500 , latest high ) ) ) or( cash ( 1 day ago close * 1 day ago volume > 100000000 and latest count( 200, 1 where( latest high / latest low ) = 1 ) < 1 and latest cmf( 21 ) > 1 day ago max( 499 , latest cmf( 21 ) ) and 1 day ago  cmf( 21 ) <= 2 day ago  max( 499 , latest cmf( 21 ) ) and 1 day ago max( 499 , latest cmf( 21 ) ) < 500 days ago max( 500 , latest cmf( 21 ) ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1 | Inequality test: left expression must be strictly less than right. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily high crossed above 20 days ago max( 480 ,  daily high ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. |
| 4 | 5 | Enabled | root/group[cash\|all] | 20 days ago max( 480 ,  daily high ) < 500 days ago max( 500 ,  daily high ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. |
| 5 | 7 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 6 | 8 | Enabled | root/group[cash\|all] | daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1 | Inequality test: left expression must be strictly less than right. |
| 7 | 9 | Enabled | root/group[cash\|all] | daily cmf( 21 ) crossed above 1 day ago max( 499 ,  daily cmf( 21 ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. |
| 8 | 10 | Enabled | root/group[cash\|all] | 1 day ago max( 499 ,  daily cmf( 21 ) ) < 500 days ago max( 500 ,  daily cmf( 21 ) ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1` — Inequality test: left expression must be strictly less than right.
- **#4** `daily high crossed above 20 days ago max( 480 ,  daily high )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars.
- **#5** `20 days ago max( 480 ,  daily high ) < 500 days ago max( 500 ,  daily high )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars.
- **#7** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#8** `daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1` — Inequality test: left expression must be strictly less than right.
- **#9** `daily cmf( 21 ) crossed above 1 day ago max( 499 ,  daily cmf( 21 ) )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars.
- **#10** `1 day ago max( 499 ,  daily cmf( 21 ) ) < 500 days ago max( 500 ,  daily cmf( 21 ) )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars.

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
- `high` — appears 6 time(s) in the expression tree
- `max` — appears 6 time(s) in the expression tree
- `cmf` — appears 4 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `count` — appears 2 time(s) in the expression tree
- `low` — appears 2 time(s) in the expression tree

### Operators observed
- `<` — 4 occurrence(s)
- `*` — 2 occurrence(s)
- `>` — 2 occurrence(s)
- `=` — 2 occurrence(s)
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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `20_days_ago`, `21_days_ago`, `500_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Mean reversion, Breakout, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Stretch conditions can highlight exhaustion zones inside ranges when broader trend is not strongly opposed.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Mean-reversion style thresholds can **fight strong trends** and produce repeated losers in momentum markets.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery, Breakout, Momentum
- **Tags:** universe:cash, indicator:volume, timeframe:daily
- **Root universe:** cash
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

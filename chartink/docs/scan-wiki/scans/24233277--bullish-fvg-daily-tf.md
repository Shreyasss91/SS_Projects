---
scan_id: 24233277
scan_name: Bullish FVG Daily TF
source_url: https://chartink.com/screener/bullish-fvg-daily-tf-7
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery","Moving average"]
tags: ["universe:nifty-500","indicator:volume","indicator:sma","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 11
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Volume/delivery
---

# Bullish FVG Daily TF

## Source

- Chartink URL: https://chartink.com/screener/bullish-fvg-daily-tf-7
- Scan ID: `24233277`
- Slug: `bullish-fvg-daily-tf-7`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2025-10-22T10:49:00.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24233277.json](../source-snapshots/24233277.json)
- Text snapshot: [source-snapshots/24233277.txt](../source-snapshots/24233277.txt)

## What this scan is for

This is a **swing** screen over **nifty 500** with **11** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Moving average**.

The active tests, in captured order:
- daily low > 2 days ago high
- 1 day ago close > 1 day ago open
- daily abs( 1 day ago close - 1 day ago open ) > ( 1 day ago high - 1 day ago low ) * 0.6
- 1 day ago volume > 2 days ago sma( close ,  20 ) * 1.5
- 2 days ago close < 2 days ago open
- daily close > daily open
- daily close < daily open
- daily abs( daily close - daily open ) < ( daily high - daily low ) * 0.3
- daily close > daily greatest
- 1 day ago close > 2 days ago high
- 100 * ( ( 1 day ago close - 1 day ago open ) / 1 day ago open ) > 1.5

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Bullish FVG Daily TF
Scan id: 24233277
Slug: bullish-fvg-daily-tf-7
Source URL: https://chartink.com/screener/bullish-fvg-daily-tf-7
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-10-22T10:49:00.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily low > 2 days ago high
2. [Enabled] 1 day ago close > 1 day ago open
3. [Enabled] daily abs( 1 day ago close - 1 day ago open ) > ( 1 day ago high - 1 day ago low ) * 0.6
4. [Enabled] 1 day ago volume > 2 days ago sma( close ,  20 ) * 1.5
5. [Enabled] 2 days ago close < 2 days ago open
6. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
7. [Enabled] daily close > daily open
    group_path: root/group[cash|any]
8. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|any]/group[cash|all])
9. [Enabled] daily close < daily open
    group_path: root/group[cash|any]/group[cash|all]
10. [Enabled] daily abs( daily close - daily open ) < ( daily high - daily low ) * 0.3
    group_path: root/group[cash|any]/group[cash|all]
11. [Enabled] daily close > daily greatest
12. [Enabled] 1 day ago close > 2 days ago high
13. [Enabled] 100 * ( ( 1 day ago close - 1 day ago open ) / 1 day ago open ) > 1.5

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 500 ( daily low > 2 days ago high and 1 day ago close > 1 day ago open and abs( 1 day ago close - 1 day ago open ) > ( 1 day ago high - 1 day ago low ) * 0.6 and 1 day ago volume > 2 days ago sma( daily volume , 20 ) * 1.5 and 2 days ago close < 2 days ago open and( cash ( daily close > daily open or( cash ( daily close < daily open and abs( daily close - daily open ) < ( daily high - daily low ) * 0.3 ) ) ) ) and daily close > greatest(  2 days ago close, 2 days ago open  ) and 1 day ago close > 2 days ago high and 100 * ( ( 1 day ago close - 1 day ago open ) / 1 day ago open ) > 1.5 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily low > 2 days ago high | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | 1 day ago close > 1 day ago open | Inequality test: left expression must be strictly greater than right. |
| 3 | 3 | Enabled | root | daily abs( 1 day ago close - 1 day ago open ) > ( 1 day ago high - 1 day ago low ) * 0.6 | Inequality test: left expression must be strictly greater than right. |
| 4 | 4 | Enabled | root | 1 day ago volume > 2 days ago sma( close ,  20 ) * 1.5 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 5 | 5 | Enabled | root | 2 days ago close < 2 days ago open | Inequality test: left expression must be strictly less than right. |
| 6 | 7 | Enabled | root/group[cash\|any] | daily close > daily open | Inequality test: left expression must be strictly greater than right. |
| 7 | 9 | Enabled | root/group[cash\|any]/group[cash\|all] | daily close < daily open | Inequality test: left expression must be strictly less than right. |
| 8 | 10 | Enabled | root/group[cash\|any]/group[cash\|all] | daily abs( daily close - daily open ) < ( daily high - daily low ) * 0.3 | Inequality test: left expression must be strictly less than right. |
| 9 | 11 | Enabled | root | daily close > daily greatest | Inequality test: left expression must be strictly greater than right. |
| 10 | 12 | Enabled | root | 1 day ago close > 2 days ago high | Inequality test: left expression must be strictly greater than right. |
| 11 | 13 | Enabled | root | 100 * ( ( 1 day ago close - 1 day ago open ) / 1 day ago open ) > 1.5 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **11** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily low > 2 days ago high` — Inequality test: left expression must be strictly greater than right.
- **#2** `1 day ago close > 1 day ago open` — Inequality test: left expression must be strictly greater than right.
- **#3** `daily abs( 1 day ago close - 1 day ago open ) > ( 1 day ago high - 1 day ago low ) * 0.6` — Inequality test: left expression must be strictly greater than right.
- **#4** `1 day ago volume > 2 days ago sma( close ,  20 ) * 1.5` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#5** `2 days ago close < 2 days ago open` — Inequality test: left expression must be strictly less than right.
- **#7** `daily close > daily open` — Inequality test: left expression must be strictly greater than right.
- **#9** `daily close < daily open` — Inequality test: left expression must be strictly less than right.
- **#10** `daily abs( daily close - daily open ) < ( daily high - daily low ) * 0.3` — Inequality test: left expression must be strictly less than right.
- **#11** `daily close > daily greatest` — Inequality test: left expression must be strictly greater than right.
- **#12** `1 day ago close > 2 days ago high` — Inequality test: left expression must be strictly greater than right.
- **#13** `100 * ( ( 1 day ago close - 1 day ago open ) / 1 day ago open ) > 1.5` — Inequality test: left expression must be strictly greater than right.

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
- `close` — appears 10 time(s) in the expression tree
- `open` — appears 9 time(s) in the expression tree
- `high` — appears 4 time(s) in the expression tree
- `low` — appears 3 time(s) in the expression tree
- `abs` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree
- `greatest` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 8 occurrence(s)
- `*` — 4 occurrence(s)
- `<` — 3 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **nifty 500**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Moving average, Volume/delivery, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **11** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery, Moving average
- **Tags:** universe:nifty-500, indicator:volume, indicator:sma, timeframe:daily
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

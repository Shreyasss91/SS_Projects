---
scan_id: 13929589
scan_name: trend change to bull
source_url: https://chartink.com/screener/trend-change-to-bull-2
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery","Volatility","Moving average"]
tags: ["universe:cash","indicator:volume","indicator:sma","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# trend change to bull

## Source

- Chartink URL: https://chartink.com/screener/trend-change-to-bull-2
- Scan ID: `13929589`
- Slug: `trend-change-to-bull-2`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-11-24T05:57:39.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/13929589.json](../source-snapshots/13929589.json)
- Text snapshot: [source-snapshots/13929589.txt](../source-snapshots/13929589.txt)

## What this scan is for

This is a **swing** screen over **cash** with **5** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Volatility, Moving average**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- ( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3
- daily close > 50
- daily % change > 8
- daily volume > 1 day ago sma( close ,  7 ) * 15

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: trend change to bull
Scan id: 13929589
Slug: trend-change-to-bull-2
Source URL: https://chartink.com/screener/trend-change-to-bull-2
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-11-24T05:57:39.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] ( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3
    group_path: root/group[cash|all]
4. [Enabled] daily close > 50
    group_path: root/group[cash|all]
5. [Enabled] daily % change > 8
6. [Enabled] daily volume > 1 day ago sma( close ,  7 ) * 15

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and( latest avg true range( 7 ) / latest sma( latest close , 7 ) ) * 100 > 3 and latest close > 50 ) ) and latest "close - 1 candle ago close / 1 candle ago close * 100" > 8 and latest volume > 1 day ago sma( latest volume , 7 ) * 15 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | ( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. ATR measures smoothed true range (volatility), not direction. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily close > 50 | Inequality test: left expression must be strictly greater than right. |
| 4 | 5 | Enabled | root | daily % change > 8 | Inequality test: left expression must be strictly greater than right. |
| 5 | 6 | Enabled | root | daily volume > 1 day ago sma( close ,  7 ) * 15 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `( daily avg true range( 7 ) / daily sma( close ,  7 ) ) * 100 > 3` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. ATR measures smoothed true range (volatility), not direction.
- **#4** `daily close > 50` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily % change > 8` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily volume > 1 day ago sma( close ,  7 ) * 15` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.

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
- `close` — appears 3 time(s) in the expression tree
- `volume` — appears 3 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree
- `avg true range` — appears 1 time(s) in the expression tree
- `% change` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 5 occurrence(s)
- `*` — 3 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Price action, Trend following, Volatility, Volume/delivery, Multi-factor.
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
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery, Volatility, Moving average
- **Tags:** universe:cash, indicator:volume, indicator:sma, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 1432131
scan_name: MULTIPLE HULLMA BUNDLING -- HOURLY
source_url: https://chartink.com/screener/multiple-hullma-bundling-hourly
market: Indian equities
horizon: Intraday
classification: ["Moving average"]
tags: ["universe:nifty-50", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Moving average
---

# MULTIPLE HULLMA BUNDLING -- HOURLY

## Source

- Chartink URL: https://chartink.com/screener/multiple-hullma-bundling-hourly
- Scan ID: `1432131`
- Slug: `multiple-hullma-bundling-hourly`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2019-11-18T19:21:55.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1432131.json](../source-snapshots/1432131.json)
- Text snapshot: [source-snapshots/1432131.txt](../source-snapshots/1432131.txt)

## What this scan is for

This is a **intraday** screen over **nifty 500** with **3** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average**.
The active tests, in captured order, are:
- ( daily abs( [-1] 60 minute wma( (2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 60 minute wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( [-1] 60 minute close / 200 )
- ( daily abs( [-1] 60 minute wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 60 minute wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( [-1] 60 minute close / 200 )
- ( daily abs( [-1] 60 minute close - ( [-1] 60 minute wma( (2 * wma(close,100) - wma(close,200) ),14 ) ) ) ) <= ( [-1] 60 minute close / 100 )

Author description (source metadata): Hull MA= WMA (2*WMA (n/2) − WMA (n)), sqrt (n))
na = 20
sqrt(20) = 4.4(rounding off to 4)

TIMEFRAME:DAILY
LATEST (HULLMA(200) - HULLMA(400)) < 0.5% OF LATEST CLOSE ==> HULLMA(200) AND HULL(400) ARE VERY CLOSE

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: MULTIPLE HULLMA BUNDLING -- HOURLY
Scan id: 1432131
Slug: multiple-hullma-bundling-hourly
Source URL: https://chartink.com/screener/multiple-hullma-bundling-hourly
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-18T19:21:55.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] ( daily abs( [-1] 60 minute wma( (2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 60 minute wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( [-1] 60 minute close / 200 )
2. [Enabled] ( daily abs( [-1] 60 minute wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 60 minute wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( [-1] 60 minute close / 200 )
3. [Enabled] ( daily abs( [-1] 60 minute close - ( [-1] 60 minute wma( (2 * wma(close,100) - wma(close,200) ),14 ) ) ) ) <= ( [-1] 60 minute close / 100 )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 500 ( ( abs( [-1] 1 hour wma( (2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 1 hour wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( [-1] 1 hour close / 200 ) and( abs( [-1] 1 hour wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 1 hour wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( [-1] 1 hour close / 200 ) and( abs( [-1] 1 hour close - ( [-1] 1 hour wma( (2 * wma(close,100) - wma(close,200) ),14 ) ) ) ) <= ( [-1] 1 hour close / 100 ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | ( daily abs( [-1] 60 minute wma( (2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 60 minute wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( [-1] 60 minute close / 200 ) | Inequality test: left expression must be less than or equal to right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 2 | Enabled | root | ( daily abs( [-1] 60 minute wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 60 minute wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( [-1] 60 minute close / 200 ) | Inequality test: left expression must be less than or equal to right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 3 | Enabled | root | ( daily abs( [-1] 60 minute close - ( [-1] 60 minute wma( (2 * wma(close,100) - wma(close,200) ),14 ) ) ) ) <= ( [-1] 60 minute close / 100 ) | Inequality test: left expression must be less than or equal to right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `( daily abs( [-1] 60 minute wma( (2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 60 minute wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( [-1] 60 minute close / 200 )` — Inequality test: left expression must be less than or equal to right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#2** `( daily abs( [-1] 60 minute wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - [-1] 60 minute wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( [-1] 60 minute close / 200 )` — Inequality test: left expression must be less than or equal to right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#3** `( daily abs( [-1] 60 minute close - ( [-1] 60 minute wma( (2 * wma(close,100) - wma(close,200) ),14 ) ) ) ) <= ( [-1] 60 minute close / 100 )` — Inequality test: left expression must be less than or equal to right. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `wma` — appears 5 time(s) in the expression tree
- `close` — appears 4 time(s) in the expression tree
- `abs` — appears 3 time(s) in the expression tree

### Operators observed
- `<=` — 3 occurrence(s)

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
- Timeframe tokens: `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Moving average
- **Tags:** universe:nifty-50, timeframe:intraday-bars
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

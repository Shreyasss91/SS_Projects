---
scan_id: 11682735
scan_name: "Copy - MACD HOOK by @StocksbyPrakhar"
source_url: https://chartink.com/screener/copy-macd-hook-by-atstocksbyprakhar-86
market: Indian equities
horizon: Swing
classification: ["Fundamental", "Moving average", "Oscillator", "Volume/delivery", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-200", "indicator:macd", "indicator:volume", "indicator:ema", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 11
disabled_filter_count: 1
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Fundamental
---

# Copy - MACD HOOK by @StocksbyPrakhar

## Source

- Chartink URL: https://chartink.com/screener/copy-macd-hook-by-atstocksbyprakhar-86
- Scan ID: `11682735`
- Slug: `copy-macd-hook-by-atstocksbyprakhar-86`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-05-08T04:11:26.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11682735.json](../source-snapshots/11682735.json)
- Text snapshot: [source-snapshots/11682735.txt](../source-snapshots/11682735.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **11** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Fundamental, Moving average, Oscillator, Volume/delivery, Multi-factor**.
The active tests, in captured order, are:
- daily macd line( 26,12,9 ) > 0
- daily macd signal( 26,12,9 ) > 0
- daily ema( close ,  8 ) > daily ema( close ,  13 )
- ( daily macd line( 26,12,9 ) - daily macd signal( 26,12,9 ) ) / daily macd signal( 26,12,9 ) < 0.05
- ( daily macd line( 26,12,9 ) - daily macd signal( 26,12,9 ) ) / daily macd signal( 26,12,9 ) > 0
- daily close > daily ema( close ,  20 )
- daily ema( close ,  20 ) > daily ema( close ,  50 )
- daily close > 20
- daily sma( close ,  50 ) > 5000
- daily count streak( 10, 1 where daily macd line( 26,12,9 ) >= daily macd signal( 26,12,9 ) ) = 10
- daily market cap > 100

Author description (source metadata): Hook Pattern

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - MACD HOOK by @StocksbyPrakhar
Scan id: 11682735
Slug: copy-macd-hook-by-atstocksbyprakhar-86
Source URL: https://chartink.com/screener/copy-macd-hook-by-atstocksbyprakhar-86
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-05-08T04:11:26.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily macd line( 26,12,9 ) > 0
2. [Enabled] daily macd signal( 26,12,9 ) > 0
3. [Enabled] daily ema( close ,  8 ) > daily ema( close ,  13 )
4. [Enabled] ( daily macd line( 26,12,9 ) - daily macd signal( 26,12,9 ) ) / daily macd signal( 26,12,9 ) < 0.05
5. [Enabled] ( daily macd line( 26,12,9 ) - daily macd signal( 26,12,9 ) ) / daily macd signal( 26,12,9 ) > 0
6. [Enabled] daily close > daily ema( close ,  20 )
7. [Enabled] daily ema( close ,  20 ) > daily ema( close ,  50 )
8. [Enabled] daily close > 20
9. [Enabled] daily sma( close ,  50 ) > 5000
10. [Enabled] daily count streak( 10, 1 where daily macd line( 26,12,9 ) >= daily macd signal( 26,12,9 ) ) = 10
11. [Disabled] daily close - daily low > ( daily high - daily low ) * 0.75
12. [Enabled] daily market cap > 100

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( latest macd line( 26,12,9 ) > 0 and latest macd signal( 26,12,9 ) > 0 and latest ema( latest macd signal( 26,12,9 ) , 8 ) > latest ema( latest macd signal( 26,12,9 ) , 13 ) and( latest macd line( 26,12,9 ) - latest macd signal( 26,12,9 ) ) / latest macd signal( 26,12,9 ) < 0.05 and( latest macd line( 26,12,9 ) - latest macd signal( 26,12,9 ) ) / latest macd signal( 26,12,9 ) > 0 and latest close > latest ema( latest close , 20 ) and latest ema( latest close , 20 ) > latest ema( latest close , 50 ) and latest close > 20 and latest sma( latest volume , 50 ) > 5000 and latest countstreak( 10, 1 where latest macd line( 26,12,9 ) >= latest macd signal( 26,12,9 ) ) = 10 and market cap > 100 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily macd line( 26,12,9 ) > 0 | Inequality test: left expression must be strictly greater than right. MACD uses EMA differences (line/signal/histogram depending on field). |
| 2 | 2 | Enabled | root | daily macd signal( 26,12,9 ) > 0 | Inequality test: left expression must be strictly greater than right. MACD uses EMA differences (line/signal/histogram depending on field). |
| 3 | 3 | Enabled | root | daily ema( close ,  8 ) > daily ema( close ,  13 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 4 | 4 | Enabled | root | ( daily macd line( 26,12,9 ) - daily macd signal( 26,12,9 ) ) / daily macd signal( 26,12,9 ) < 0.05 | Inequality test: left expression must be strictly less than right. MACD uses EMA differences (line/signal/histogram depending on field). |
| 5 | 5 | Enabled | root | ( daily macd line( 26,12,9 ) - daily macd signal( 26,12,9 ) ) / daily macd signal( 26,12,9 ) > 0 | Inequality test: left expression must be strictly greater than right. MACD uses EMA differences (line/signal/histogram depending on field). |
| 6 | 6 | Enabled | root | daily close > daily ema( close ,  20 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 7 | 7 | Enabled | root | daily ema( close ,  20 ) > daily ema( close ,  50 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. |
| 8 | 8 | Enabled | root | daily close > 20 | Inequality test: left expression must be strictly greater than right. |
| 9 | 9 | Enabled | root | daily sma( close ,  50 ) > 5000 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 10 | 10 | Enabled | root | daily count streak( 10, 1 where daily macd line( 26,12,9 ) >= daily macd signal( 26,12,9 ) ) = 10 | Inequality test: left expression must be greater than or equal to right. MACD uses EMA differences (line/signal/histogram depending on field). |
| 11 | 11 | Disabled | root | daily close - daily low > ( daily high - daily low ) * 0.75 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 12 | 12 | Enabled | root | daily market cap > 100 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **11** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily macd line( 26,12,9 ) > 0` — Inequality test: left expression must be strictly greater than right. MACD uses EMA differences (line/signal/histogram depending on field).
- **#2** `daily macd signal( 26,12,9 ) > 0` — Inequality test: left expression must be strictly greater than right. MACD uses EMA differences (line/signal/histogram depending on field).
- **#3** `daily ema( close ,  8 ) > daily ema( close ,  13 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#4** `( daily macd line( 26,12,9 ) - daily macd signal( 26,12,9 ) ) / daily macd signal( 26,12,9 ) < 0.05` — Inequality test: left expression must be strictly less than right. MACD uses EMA differences (line/signal/histogram depending on field).
- **#5** `( daily macd line( 26,12,9 ) - daily macd signal( 26,12,9 ) ) / daily macd signal( 26,12,9 ) > 0` — Inequality test: left expression must be strictly greater than right. MACD uses EMA differences (line/signal/histogram depending on field).
- **#6** `daily close > daily ema( close ,  20 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#7** `daily ema( close ,  20 ) > daily ema( close ,  50 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field.
- **#8** `daily close > 20` — Inequality test: left expression must be strictly greater than right.
- **#9** `daily sma( close ,  50 ) > 5000` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#10** `daily count streak( 10, 1 where daily macd line( 26,12,9 ) >= daily macd signal( 26,12,9 ) ) = 10` — Inequality test: left expression must be greater than or equal to right. MACD uses EMA differences (line/signal/histogram depending on field).
- **#12** `daily market cap > 100` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **1** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #11
- **Condition (verbatim):** `daily close - daily low > ( daily high - daily low ) * 0.75`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `macd signal` — appears 8 time(s) in the expression tree
- `close` — appears 6 time(s) in the expression tree
- `ema` — appears 5 time(s) in the expression tree
- `macd line` — appears 4 time(s) in the expression tree
- `low` — appears 2 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `count streak` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 10 occurrence(s)
- `/` — 2 occurrence(s)
- `<` — 1 occurrence(s)
- `=` — 1 occurrence(s)
- `>=` — 1 occurrence(s)
- `-` — 1 occurrence(s)
- `*` — 1 occurrence(s)

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
- **Method context:** Fundamental, Moving average, Oscillator, Volume/delivery, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **11** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **1** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Fundamental, Moving average, Oscillator, Volume/delivery, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-200, indicator:macd, indicator:volume, indicator:ema, indicator:sma, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

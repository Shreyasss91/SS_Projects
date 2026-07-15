---
scan_id: 4781065
scan_name: Copy - Volume Shockers (stocks with rising volumes) by Amitabhjha3
source_url: https://chartink.com/screener/copy-volume-shockers-stocks-with-rising-volumes-by-amitabhjha3-1
market: Indian equities
horizon: "Multi-horizon"
classification: ["Volume/delivery","Moving average","Fundamental","Oscillator"]
tags: ["universe:cash","indicator:volume","indicator:sma","indicator:rsi","indicator:ema","timeframe:daily","timeframe:weekly","timeframe:monthly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# Copy - Volume Shockers (stocks with rising volumes) by Amitabhjha3

## Source

- Chartink URL: https://chartink.com/screener/copy-volume-shockers-stocks-with-rising-volumes-by-amitabhjha3-1
- Scan ID: `4781065`
- Slug: `copy-volume-shockers-stocks-with-rising-volumes-by-amitabhjha3-1`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2021-06-02T17:27:55.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4781065.json](../source-snapshots/4781065.json)
- Text snapshot: [source-snapshots/4781065.txt](../source-snapshots/4781065.txt)

## What this scan is for

This is a **multi-horizon** screen over **cash** with **8** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Moving average, Fundamental, Oscillator**.

The active tests, in captured order:
- daily volume > daily sma( volume,10 ) * 2
- daily % change <= 10
- daily close > 1 day ago close * 1.05
- daily close < 1 day ago close * 0.95
- daily market cap >= 100
- weekly rsi( 14 ) >= 60
- daily rsi( 14 ) >= 55
- daily close >= daily ema( close ,  20 )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - Volume Shockers (stocks with rising volumes) by Amitabhjha3
Scan id: 4781065
Slug: copy-volume-shockers-stocks-with-rising-volumes-by-amitabhjha3-1
Source URL: https://chartink.com/screener/copy-volume-shockers-stocks-with-rising-volumes-by-amitabhjha3-1
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-02T17:27:55.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily volume > daily sma( volume,10 ) * 2
2. [Enabled] daily % change <= 10
3. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
4. [Enabled] daily close > 1 day ago close * 1.05
    group_path: root/group[cash|any]
5. [Enabled] daily close < 1 day ago close * 0.95
    group_path: root/group[cash|any]
6. [Enabled] daily market cap >= 100
7. [Enabled] weekly rsi( 14 ) >= 60
8. [Enabled] daily rsi( 14 ) >= 55
9. [Enabled] daily close >= daily ema( close ,  20 )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( latest volume > latest sma( volume,10 ) * 2 and latest "close - 1 candle ago close / 1 candle ago close * 100" <= 10 and( cash ( latest close > 1 day ago close * 1.05 or latest close < 1 day ago close * 0.95 ) ) and market cap >= 100 and weekly rsi( 14 ) >= 60 and latest rsi( 14 ) >= 55 and latest close >= latest ema( latest close , 20 ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily volume > daily sma( volume,10 ) * 2 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 2 | 2 | Enabled | root | daily % change <= 10 | Inequality test: left expression must be less than or equal to right. |
| 3 | 4 | Enabled | root/group[cash\|any] | daily close > 1 day ago close * 1.05 | Inequality test: left expression must be strictly greater than right. |
| 4 | 5 | Enabled | root/group[cash\|any] | daily close < 1 day ago close * 0.95 | Inequality test: left expression must be strictly less than right. |
| 5 | 6 | Enabled | root | daily market cap >= 100 | Inequality test: left expression must be greater than or equal to right. Filters by market-capitalisation field from Chartink fundamentals. |
| 6 | 7 | Enabled | root | weekly rsi( 14 ) >= 60 | Inequality test: left expression must be greater than or equal to right. RSI is a momentum oscillator from average gains/losses over its period. References weekly bars / weekly offset. |
| 7 | 8 | Enabled | root | daily rsi( 14 ) >= 55 | Inequality test: left expression must be greater than or equal to right. RSI is a momentum oscillator from average gains/losses over its period. |
| 8 | 9 | Enabled | root | daily close >= daily ema( close ,  20 ) | Inequality test: left expression must be greater than or equal to right. EMA is an exponentially weighted moving average of the chosen field. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily volume > daily sma( volume,10 ) * 2` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#2** `daily % change <= 10` — Inequality test: left expression must be less than or equal to right.
- **#4** `daily close > 1 day ago close * 1.05` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily close < 1 day ago close * 0.95` — Inequality test: left expression must be strictly less than right.
- **#6** `daily market cap >= 100` — Inequality test: left expression must be greater than or equal to right. Filters by market-capitalisation field from Chartink fundamentals.
- **#7** `weekly rsi( 14 ) >= 60` — Inequality test: left expression must be greater than or equal to right. RSI is a momentum oscillator from average gains/losses over its period. References weekly bars / weekly offset.
- **#8** `daily rsi( 14 ) >= 55` — Inequality test: left expression must be greater than or equal to right. RSI is a momentum oscillator from average gains/losses over its period.
- **#9** `daily close >= daily ema( close ,  20 )` — Inequality test: left expression must be greater than or equal to right. EMA is an exponentially weighted moving average of the chosen field.

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
- `close` — appears 6 time(s) in the expression tree
- `rsi` — appears 2 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree
- `% change` — appears 1 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree
- `ema` — appears 1 time(s) in the expression tree

### Operators observed
- `>=` — 4 occurrence(s)
- `*` — 3 occurrence(s)
- `>` — 2 occurrence(s)
- `<=` — 1 occurrence(s)
- `<` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `0_weeks_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Oscillator, Fundamental, Moving average, Price action, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Volume/delivery, Moving average, Fundamental, Oscillator
- **Tags:** universe:cash, indicator:volume, indicator:sma, indicator:rsi, indicator:ema, timeframe:daily, timeframe:weekly, timeframe:monthly
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

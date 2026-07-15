---
scan_id: 25160125
scan_name: Stocks to Buy WeeklyTF
source_url: https://chartink.com/screener/stocks-to-buy-weeklytf
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery","Moving average","Volatility","Fundamental","Oscillator","Breakout","Momentum"]
tags: ["universe:cash","indicator:volume","indicator:rsi","timeframe:weekly","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 9
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# Stocks to Buy WeeklyTF

## Source

- Chartink URL: https://chartink.com/screener/stocks-to-buy-weeklytf
- Scan ID: `25160125`
- Slug: `stocks-to-buy-weeklytf`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2026-01-24T02:19:45.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/25160125.json](../source-snapshots/25160125.json)
- Text snapshot: [source-snapshots/25160125.txt](../source-snapshots/25160125.txt)

## What this scan is for

This is a **swing** screen over **cash** with **9** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Moving average, Volatility, Fundamental, Oscillator, Breakout, Momentum**.

The active tests, in captured order:
- weekly volume > 1 week ago volume * 1.8
- weekly high crossed above 1 week ago max( 6 ,  weekly high )
- 1 week ago high < 2 weeks ago max( 6 ,  weekly high )
- weekly ichimoku conversion line( 9 ,  26 ,  52 ) > weekly ichimoku base line( 9 ,  26 ,  52 )
- weekly ichimoku conversion line( 9 ,  26 ,  52 ) < weekly ichimoku base line( 9 ,  26 ,  52 ) + ( weekly avg true range( 14 ) * 1 )
- weekly avg true range( 1 ) > 1 week ago avg true range( 14 )
- daily market cap > 1000
- weekly rsi( 14 ) > 1 week ago rsi( 14 )
- weekly rsi( 14 ) > 45

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Stocks to Buy WeeklyTF
Scan id: 25160125
Slug: stocks-to-buy-weeklytf
Source URL: https://chartink.com/screener/stocks-to-buy-weeklytf
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2026-01-24T02:19:45.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
2. [Enabled] weekly volume > 1 week ago volume * 1.8
    group_path: root/group[cash|any]
3. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|any]/group[cash|all])
4. [Enabled] weekly high crossed above 1 week ago max( 6 ,  weekly high )
    group_path: root/group[cash|any]/group[cash|all]
5. [Enabled] 1 week ago high < 2 weeks ago max( 6 ,  weekly high )
    group_path: root/group[cash|any]/group[cash|all]
6. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Enabled] weekly ichimoku conversion line( 9 ,  26 ,  52 ) > weekly ichimoku base line( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
8. [Enabled] weekly ichimoku conversion line( 9 ,  26 ,  52 ) < weekly ichimoku base line( 9 ,  26 ,  52 ) + ( weekly avg true range( 14 ) * 1 )
    group_path: root/group[cash|all]
9. [Enabled] weekly avg true range( 1 ) > 1 week ago avg true range( 14 )
10. [Enabled] daily market cap > 1000
11. [Enabled] weekly rsi( 14 ) > 1 week ago rsi( 14 )
12. [Enabled] weekly rsi( 14 ) > 45

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash (  weekly volume >  1 week ago volume *  1.8 or( cash (  weekly high >  1 week ago max( 6 ,  weekly high ) and  1 week ago  high <=  2 week ago  max( 6 ,  weekly high ) and  1 week ago high <  2 weeks ago max( 6 ,  weekly high ) ) ) ) ) and( cash (  weekly ichimoku conversion line( 9 , 26 , 52 ) >  weekly ichimoku base line( 9 , 26 , 52 ) and  weekly ichimoku conversion line( 9 , 26 , 52 ) <  weekly ichimoku base line( 9 , 26 , 52 ) +  (  weekly avg true range( 14 ) *  1 ) ) ) and  weekly avg true range( 1 ) >  1 week ago avg true range( 14 ) and  market cap >  1000 and  weekly rsi( 14 ) >  1 week ago rsi( 14 ) and  weekly rsi( 14 ) >  45 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|any] | weekly volume > 1 week ago volume * 1.8 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. References weekly bars / weekly offset. |
| 2 | 4 | Enabled | root/group[cash\|any]/group[cash\|all] | weekly high crossed above 1 week ago max( 6 ,  weekly high ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 3 | 5 | Enabled | root/group[cash\|any]/group[cash\|all] | 1 week ago high < 2 weeks ago max( 6 ,  weekly high ) | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 4 | 7 | Enabled | root/group[cash\|all] | weekly ichimoku conversion line( 9 ,  26 ,  52 ) > weekly ichimoku base line( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. References weekly bars / weekly offset. |
| 5 | 8 | Enabled | root/group[cash\|all] | weekly ichimoku conversion line( 9 ,  26 ,  52 ) < weekly ichimoku base line( 9 ,  26 ,  52 ) + ( weekly avg true range( 14 ) * 1 ) | Inequality test: left expression must be strictly less than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. ATR measures smoothed true range (volatility), not direction. |
| 6 | 9 | Enabled | root | weekly avg true range( 1 ) > 1 week ago avg true range( 14 ) | Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. References weekly bars / weekly offset. |
| 7 | 10 | Enabled | root | daily market cap > 1000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 8 | 11 | Enabled | root | weekly rsi( 14 ) > 1 week ago rsi( 14 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. References weekly bars / weekly offset. |
| 9 | 12 | Enabled | root | weekly rsi( 14 ) > 45 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. References weekly bars / weekly offset. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **9** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `weekly volume > 1 week ago volume * 1.8` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. References weekly bars / weekly offset.
- **#4** `weekly high crossed above 1 week ago max( 6 ,  weekly high )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#5** `1 week ago high < 2 weeks ago max( 6 ,  weekly high )` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#7** `weekly ichimoku conversion line( 9 ,  26 ,  52 ) > weekly ichimoku base line( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. References weekly bars / weekly offset.
- **#8** `weekly ichimoku conversion line( 9 ,  26 ,  52 ) < weekly ichimoku base line( 9 ,  26 ,  52 ) + ( weekly avg true range( 14 ) * 1 )` — Inequality test: left expression must be strictly less than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. ATR measures smoothed true range (volatility), not direction.
- **#9** `weekly avg true range( 1 ) > 1 week ago avg true range( 14 )` — Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. References weekly bars / weekly offset.
- **#10** `daily market cap > 1000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#11** `weekly rsi( 14 ) > 1 week ago rsi( 14 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. References weekly bars / weekly offset.
- **#12** `weekly rsi( 14 ) > 45` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. References weekly bars / weekly offset.

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
- `high` — appears 4 time(s) in the expression tree
- `avg true range` — appears 3 time(s) in the expression tree
- `rsi` — appears 3 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `ichimoku conversion line` — appears 2 time(s) in the expression tree
- `ichimoku base line` — appears 2 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 6 occurrence(s)
- `<` — 2 occurrence(s)
- `*` — 1 occurrence(s)
- `crossed above` — 1 occurrence(s)
- `+` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `1_weeks_ago`, `2_weeks_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Fundamental, Moving average, Volatility, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **9** active filters — transparent screening logic.
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

- **Horizon:** Swing
- **Methods:** Volume/delivery, Moving average, Volatility, Fundamental, Oscillator, Breakout, Momentum
- **Tags:** universe:cash, indicator:volume, indicator:rsi, timeframe:weekly, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

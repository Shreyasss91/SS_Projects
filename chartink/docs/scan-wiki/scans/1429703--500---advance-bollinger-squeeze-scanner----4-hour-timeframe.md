---
scan_id: 1429703
scan_name: "500% - Advance Bollinger Squeeze Scanner -- 4 HOUR TIMEFRAME"
source_url: https://chartink.com/screener/copy-500-advance-bollinger-squeeze-scanner-15
market: Indian equities
horizon: Intraday
classification: ["Volatility", "Moving average", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:nifty-50", "indicator:bollinger", "indicator:volume", "indicator:sma", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Volatility
---

# 500% - Advance Bollinger Squeeze Scanner -- 4 HOUR TIMEFRAME

## Source

- Chartink URL: https://chartink.com/screener/copy-500-advance-bollinger-squeeze-scanner-15
- Scan ID: `1429703`
- Slug: `copy-500-advance-bollinger-squeeze-scanner-15`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2019-11-18T05:42:43.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1429703.json](../source-snapshots/1429703.json)
- Text snapshot: [source-snapshots/1429703.txt](../source-snapshots/1429703.txt)

## What this scan is for

This scan, titled "500% - Advance Bollinger Squeeze Scanner -- 4 HOUR TIMEFRAME", appears designed to screen Indian equities in the **nifty 500** universe using **8 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Volatility, Moving average, Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `240_minute`.

Author description (source metadata): Advance Bollinger Squeeze Scanner
(https://chartink.com/screener/copy-advance-bollinger-squeeze-scanner-8 -- DAILY TIMEFRAME)

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: 500% - Advance Bollinger Squeeze Scanner -- 4 HOUR TIMEFRAME
Scan id: 1429703
Slug: copy-500-advance-bollinger-squeeze-scanner-15
Source URL: https://chartink.com/screener/copy-500-advance-bollinger-squeeze-scanner-15
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-18T05:42:43.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] ( ( ( [-2] 240 minute upper bollinger band( 20,2 ) - [-1] 240 minute upper bollinger band( 20,2 ) ) * 100 ) / [-2] 240 minute upper bollinger band( 20,2 ) ) > -1
2. [Enabled] ( ( ( [-1] 240 minute lower bollinger band( 20,2 ) - [-2] 240 minute lower bollinger band( 20,2 ) ) * 100 ) / [-1] 240 minute lower bollinger band( 20,2 ) ) > -1
3. [Enabled] [0] 240 minute close > [0] 240 minute open
4. [Enabled] [0] 240 minute volume > [0] 240 minute sma( volume,10 ) * 2
5. [Enabled] ( ( ( [0] 240 minute upper bollinger band( 20,2 ) - [-1] 240 minute upper bollinger band( 20,2 ) ) * 100 ) / [0] 240 minute upper bollinger band( 20,2 ) ) >= 1.5
6. [Enabled] ( ( ( [-1] 240 minute lower bollinger band( 20,2 ) - [0] 240 minute lower bollinger band( 20,2 ) ) * 100 ) / [-1] 240 minute lower bollinger band( 20,2 ) ) > 0
7. [Enabled] [0] 240 minute close > [0] 240 minute upper bollinger band( 20,2 )
8. [Enabled] [-1] 240 minute close crossed above [0] 240 minute sma( close,7 )

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 500 ( ( ( ( [-2] 4 hour upper bollinger band( 20,2 ) - [-1] 4 hour upper bollinger band( 20,2 ) ) * 100 ) / [-2] 4 hour upper bollinger band( 20,2 ) ) > -1 and( ( ( [-1] 4 hour lower bollinger band( 20,2 ) - [-2] 4 hour lower bollinger band( 20,2 ) ) * 100 ) / [-1] 4 hour lower bollinger band( 20,2 ) ) > -1 and [0] 4 hour close > [0] 4 hour open and [0] 4 hour volume > [0] 4 hour sma( volume,10 ) * 2 and( ( ( [0] 4 hour upper bollinger band( 20,2 ) - [-1] 4 hour upper bollinger band( 20,2 ) ) * 100 ) / [0] 4 hour upper bollinger band( 20,2 ) ) >= 1.5 and( ( ( [-1] 4 hour lower bollinger band( 20,2 ) - [0] 4 hour lower bollinger band( 20,2 ) ) * 100 ) / [-1] 4 hour lower bollinger band( 20,2 ) ) > 0 and [0] 4 hour close > [0] 4 hour upper bollinger band( 20,2 ) and [-1] 4 hour close > [0] 4 hour sma( close,7 ) and [ -2 ] 4 hour close <= [ -1 ] 4 hour sma( close,7 ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | ( ( ( [-2] 240 minute upper bollinger band( 20,2 ) - [-1] 240 minute upper bollinger band( 20,2 ) ) * 100 ) / [-2] 240 minute upper bollinger band( 20,2 ) ) > -1 | Inequality test: left expression must be strictly greater than right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | Enabled | ( ( ( [-1] 240 minute lower bollinger band( 20,2 ) - [-2] 240 minute lower bollinger band( 20,2 ) ) * 100 ) / [-1] 240 minute lower bollinger band( 20,2 ) ) > -1 | Inequality test: left expression must be strictly greater than right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | Enabled | [0] 240 minute close > [0] 240 minute open | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | Enabled | [0] 240 minute volume > [0] 240 minute sma( volume,10 ) * 2 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | Enabled | ( ( ( [0] 240 minute upper bollinger band( 20,2 ) - [-1] 240 minute upper bollinger band( 20,2 ) ) * 100 ) / [0] 240 minute upper bollinger band( 20,2 ) ) >= 1.5 | Inequality test: left expression must be greater than or equal to right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | Enabled | ( ( ( [-1] 240 minute lower bollinger band( 20,2 ) - [0] 240 minute lower bollinger band( 20,2 ) ) * 100 ) / [-1] 240 minute lower bollinger band( 20,2 ) ) > 0 | Inequality test: left expression must be strictly greater than right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | Enabled | [0] 240 minute close > [0] 240 minute upper bollinger band( 20,2 ) | Inequality test: left expression must be strictly greater than right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | Enabled | [-1] 240 minute close crossed above [0] 240 minute sma( close,7 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `( ( ( [-2] 240 minute upper bollinger band( 20,2 ) - [-1] 240 minute upper bollinger band( 20,2 ) ) * 100 ) / [-2] 240 minute upper bollinger band( 20,2 ) ) > -1` — Inequality test: left expression must be strictly greater than right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#2** `( ( ( [-1] 240 minute lower bollinger band( 20,2 ) - [-2] 240 minute lower bollinger band( 20,2 ) ) * 100 ) / [-1] 240 minute lower bollinger band( 20,2 ) ) > -1` — Inequality test: left expression must be strictly greater than right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#3** `[0] 240 minute close > [0] 240 minute open` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `[0] 240 minute volume > [0] 240 minute sma( volume,10 ) * 2` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `( ( ( [0] 240 minute upper bollinger band( 20,2 ) - [-1] 240 minute upper bollinger band( 20,2 ) ) * 100 ) / [0] 240 minute upper bollinger band( 20,2 ) ) >= 1.5` — Inequality test: left expression must be greater than or equal to right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `( ( ( [-1] 240 minute lower bollinger band( 20,2 ) - [0] 240 minute lower bollinger band( 20,2 ) ) * 100 ) / [-1] 240 minute lower bollinger band( 20,2 ) ) > 0` — Inequality test: left expression must be strictly greater than right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[0] 240 minute close > [0] 240 minute upper bollinger band( 20,2 )` — Inequality test: left expression must be strictly greater than right. Bollinger fields are typically a moving average ± standard-deviation bands. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[-1] 240 minute close crossed above [0] 240 minute sma( close,7 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `upper bollinger band` — appears 7 time(s) in the expression tree
- `lower bollinger band` — appears 6 time(s) in the expression tree
- `close` — appears 3 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree
- `open` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 6 occurrence(s)
- `*` — 1 occurrence(s)
- `>=` — 1 occurrence(s)
- `crossed above` — 1 occurrence(s)

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
- Timeframe tokens: `240_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
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
- **Methods:** Volatility, Moving average, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:nifty-50, indicator:bollinger, indicator:volume, indicator:sma, timeframe:intraday-bars
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

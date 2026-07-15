---
scan_id: 24124918
scan_name: Ichimoku Breakout hour tf
source_url: https://chartink.com/screener/ichimoku-breakout-hour-tf
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Trend following", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "universe:nifty-200", "indicator:rsi", "indicator:ichimoku", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 20
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# Ichimoku Breakout hour tf

## Source

- Chartink URL: https://chartink.com/screener/ichimoku-breakout-hour-tf
- Scan ID: `24124918`
- Slug: `ichimoku-breakout-hour-tf`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2025-10-11T13:30:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24124918.json](../source-snapshots/24124918.json)
- Text snapshot: [source-snapshots/24124918.txt](../source-snapshots/24124918.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **20** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average, Trend following, Momentum, Multi-factor**.
The active tests, in captured order, are:
- [0] 60 minute close > [-26] 60 minute close
- [0] 60 minute close > [-25] 60 minute close
- [0] 60 minute close > [-24] 60 minute close
- [0] 60 minute close > [-23] 60 minute close
- [0] 60 minute close > [-22] 60 minute close
- [0] 60 minute close > [-21] 60 minute close
- [0] 60 minute close > [-20] 60 minute close
- [0] 60 minute close > [-19] 60 minute close
- [0] 60 minute close > [-18] 60 minute close
- [0] 60 minute close > [-17] 60 minute close
- [0] 60 minute close > [-16] 60 minute close
- [0] 60 minute close > [-15] 60 minute close
- [0] 60 minute close > [-14] 60 minute close
- [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku base line( 9 ,  26 ,  52 )
- [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span a( 9 ,  26 ,  52 )
- [0] 60 minute ichimoku base line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span a( 9 ,  26 ,  52 )
- [0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span b( 9 ,  26 ,  52 )
- [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) crossed above [0] 60 minute ichimoku base line( 9 ,  26 ,  52 )
- [0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) crossed above [0] 60 minute ichimoku span b( 9 ,  26 ,  52 )
- [0] 60 minute close crossed above [-26] 60 minute close

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Ichimoku Breakout hour tf
Scan id: 24124918
Slug: ichimoku-breakout-hour-tf
Source URL: https://chartink.com/screener/ichimoku-breakout-hour-tf
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-10-11T13:30:56.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] [0] 60 minute close > [-26] 60 minute close
    group_path: root/group[cash|all]
3. [Enabled] [0] 60 minute close > [-25] 60 minute close
    group_path: root/group[cash|all]
4. [Enabled] [0] 60 minute close > [-24] 60 minute close
    group_path: root/group[cash|all]
5. [Enabled] [0] 60 minute close > [-23] 60 minute close
    group_path: root/group[cash|all]
6. [Enabled] [0] 60 minute close > [-22] 60 minute close
    group_path: root/group[cash|all]
7. [Enabled] [0] 60 minute close > [-21] 60 minute close
    group_path: root/group[cash|all]
8. [Enabled] [0] 60 minute close > [-20] 60 minute close
    group_path: root/group[cash|all]
9. [Enabled] [0] 60 minute close > [-19] 60 minute close
    group_path: root/group[cash|all]
10. [Enabled] [0] 60 minute close > [-18] 60 minute close
    group_path: root/group[cash|all]
11. [Enabled] [0] 60 minute close > [-17] 60 minute close
    group_path: root/group[cash|all]
12. [Enabled] [0] 60 minute close > [-16] 60 minute close
    group_path: root/group[cash|all]
13. [Enabled] [0] 60 minute close > [-15] 60 minute close
    group_path: root/group[cash|all]
14. [Enabled] [0] 60 minute close > [-14] 60 minute close
    group_path: root/group[cash|all]
15. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
16. [Enabled] [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku base line( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
17. [Enabled] [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span a( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
18. [Enabled] [0] 60 minute ichimoku base line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span a( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
19. [Enabled] [0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span b( 9 ,  26 ,  52 )
    group_path: root/group[cash|all]
20. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
21. [Enabled] [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) crossed above [0] 60 minute ichimoku base line( 9 ,  26 ,  52 )
    group_path: root/group[cash|any]
22. [Enabled] [0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) crossed above [0] 60 minute ichimoku span b( 9 ,  26 ,  52 )
    group_path: root/group[cash|any]
23. [Enabled] [0] 60 minute close crossed above [-26] 60 minute close
    group_path: root/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( [0] 1 hour close > [-26] 1 hour close and [0] 1 hour close > [-25] 1 hour close and [0] 1 hour close > [-24] 1 hour close and [0] 1 hour close > [-23] 1 hour close and [0] 1 hour close > [-22] 1 hour close and [0] 1 hour close > [-21] 1 hour close and [0] 1 hour close > [-20] 1 hour close and [0] 1 hour close > [-19] 1 hour close and [0] 1 hour close > [-18] 1 hour close and [0] 1 hour close > [-17] 1 hour close and [0] 1 hour close > [-16] 1 hour close and [0] 1 hour close > [-15] 1 hour close and [0] 1 hour close > [-14] 1 hour close ) ) and( cash ( [0] 1 hour ichimoku conversion line( 9 , 26 , 52 ) > [0] 1 hour ichimoku base line( 9 , 26 , 52 ) and [0] 1 hour ichimoku conversion line( 9 , 26 , 52 ) > [0] 1 hour ichimoku span a( 9 , 26 , 52 ) and [0] 1 hour ichimoku base line( 9 , 26 , 52 ) > [0] 1 hour ichimoku span a( 9 , 26 , 52 ) and [0] 1 hour ichimoku span a( 9 , 26 , 52 ) > [0] 1 hour ichimoku span b( 9 , 26 , 52 ) ) ) and( cash ( [0] 1 hour ichimoku conversion line( 9 , 26 , 52 ) > [0] 1 hour ichimoku base line( 9 , 26 , 52 ) and [ -1 ] 1 hour ichimoku conversion line( 9 , 26 , 52 ) <= [ -1 ] 1 hour ichimoku base line( 9 , 26 , 52 ) or [0] 1 hour ichimoku span a( 9 , 26 , 52 ) > [0] 1 hour ichimoku span b( 9 , 26 , 52 ) and [ -1 ] 1 hour ichimoku span a( 9 , 26 , 52 ) <= [ -1 ] 1 hour ichimoku span b( 9 , 26 , 52 ) or [0] 1 hour close > [-26] 1 hour close and [ -1 ] 1 hour close <= [ -27 ] 1 hour close ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-26] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 3 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-25] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 4 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-24] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 5 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-23] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 6 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-22] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 7 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-21] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 8 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-20] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 9 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-19] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 10 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-18] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 11 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-17] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 12 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-16] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | 13 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-15] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | 14 | Enabled | root/group[cash\|all] | [0] 60 minute close > [-14] 60 minute close | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 14 | 16 | Enabled | root/group[cash\|all] | [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku base line( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | 17 | Enabled | root/group[cash\|all] | [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | 18 | Enabled | root/group[cash\|all] | [0] 60 minute ichimoku base line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 17 | 19 | Enabled | root/group[cash\|all] | [0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span b( 9 ,  26 ,  52 ) | Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 18 | 21 | Enabled | root/group[cash\|any] | [0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) crossed above [0] 60 minute ichimoku base line( 9 ,  26 ,  52 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 19 | 22 | Enabled | root/group[cash\|any] | [0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) crossed above [0] 60 minute ichimoku span b( 9 ,  26 ,  52 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 20 | 23 | Enabled | root/group[cash\|any] | [0] 60 minute close crossed above [-26] 60 minute close | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **20** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[0] 60 minute close > [-26] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#3** `[0] 60 minute close > [-25] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `[0] 60 minute close > [-24] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[0] 60 minute close > [-23] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[0] 60 minute close > [-22] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[0] 60 minute close > [-21] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[0] 60 minute close > [-20] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[0] 60 minute close > [-19] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[0] 60 minute close > [-18] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#11** `[0] 60 minute close > [-17] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#12** `[0] 60 minute close > [-16] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#13** `[0] 60 minute close > [-15] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#14** `[0] 60 minute close > [-14] 60 minute close` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#16** `[0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku base line( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#17** `[0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span a( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#18** `[0] 60 minute ichimoku base line( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span a( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#19** `[0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) > [0] 60 minute ichimoku span b( 9 ,  26 ,  52 )` — Inequality test: left expression must be strictly greater than right. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#21** `[0] 60 minute ichimoku conversion line( 9 ,  26 ,  52 ) crossed above [0] 60 minute ichimoku base line( 9 ,  26 ,  52 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#22** `[0] 60 minute ichimoku span a( 9 ,  26 ,  52 ) crossed above [0] 60 minute ichimoku span b( 9 ,  26 ,  52 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#23** `[0] 60 minute close crossed above [-26] 60 minute close` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `close` — appears 28 time(s) in the expression tree
- `ichimoku span a` — appears 4 time(s) in the expression tree
- `ichimoku conversion line` — appears 3 time(s) in the expression tree
- `ichimoku base line` — appears 3 time(s) in the expression tree
- `ichimoku span b` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 17 occurrence(s)
- `crossed above` — 3 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Trend following, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **20** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
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
- **Methods:** Moving average, Trend following, Momentum, Multi-factor
- **Tags:** bias:upward-condition, universe:nifty-200, indicator:rsi, indicator:ichimoku, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

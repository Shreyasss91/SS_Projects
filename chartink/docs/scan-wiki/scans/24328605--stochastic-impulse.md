---
scan_id: 24328605
scan_name: stochastic impulse
source_url: https://chartink.com/screener/stochastic-impulse
market: Indian equities
horizon: Intraday
classification: ["Oscillator", "Breakout", "Momentum", "Multi-factor"]
tags: ["universe:nifty-200", "indicator:stochastic", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: any
primary_classification: Oscillator
---

# stochastic impulse

## Source

- Chartink URL: https://chartink.com/screener/stochastic-impulse
- Scan ID: `24328605`
- Slug: `stochastic-impulse`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2025-10-31T05:02:48.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24328605.json](../source-snapshots/24328605.json)
- Text snapshot: [source-snapshots/24328605.txt](../source-snapshots/24328605.txt)

## What this scan is for

This scan, titled "stochastic impulse", appears designed to screen Indian equities in the **nifty 200** universe using **6 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Oscillator, Breakout, Momentum, Multi-factor**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 15_minute, 5_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: stochastic impulse
Scan id: 24328605
Slug: stochastic-impulse
Source URL: https://chartink.com/screener/stochastic-impulse
Root universe/segment: nifty 200
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-10-31T05:02:48.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] [0] 15 minute max( 144 ,  [0] 15 minute fast stochastic %d( 233 ,  3 ) ) - [0] 15 minute min( 144 ,  [0] 15 minute fast stochastic %d( 233 ,  3 ) ) crossed above 89
    group_path: root/group[cash|all]
3. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any])
4. [Enabled] [0] 15 minute fast stochastic %d( 233 ,  3 ) > [-144] 15 minute fast stochastic %d( 233 ,  3 )
    group_path: root/group[cash|all]/group[cash|any]
5. [Enabled] [0] 15 minute fast stochastic %d( 233 ,  3 ) < [-144] 15 minute fast stochastic %d( 233 ,  3 )
    group_path: root/group[cash|all]/group[cash|any]
6. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all])
8. [Enabled] [-144] 15 minute count( 610, 1 where [0] 15 minute fast stochastic %d( 233 ,  3 ) < 60 ) > 550
    group_path: root/group[cash|all]/group[cash|all]
9. [Enabled] [0] 15 minute count( 144, 1 where [0] 15 minute fast stochastic %d( 233 ,  3 ) > 60 ) crossed above 120
    group_path: root/group[cash|all]/group[cash|all]
10. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
11. [Enabled] [0] 5 minute count( 75, 1 where [0] 5 minute fast stochastic %d( 233 ,  3 ) > [-1] 5 minute fast stochastic %d( 233 ,  3 ) * 1.02 ) crossed above 35
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( ( cash ( [0] 15 minute max( 144 , [0] 15 minute fast stochastic %d( 233 , 3 ) ) - [0] 15 minute min( 144 , [0] 15 minute fast stochastic %d( 233 , 3 ) ) > 89 and [ -1 ] 15 minute max( 144 , [0] 15 minute fast stochastic %d( 233 , 3 ) )- [ -1 ] 15 minute min( 144 , [0] 15 minute fast stochastic %d( 233 , 3 ) )<= 89 and( cash ( [0] 15 minute fast stochastic %d( 233 , 3 ) > [-144] 15 minute fast stochastic %d( 233 , 3 ) or [0] 15 minute fast stochastic %d( 233 , 3 ) < [-144] 15 minute fast stochastic %d( 233 , 3 ) ) ) ) ) or( cash ( [0] 5 minute count( 75, 1 where [0] 5 minute fast stochastic %d( 233 , 3 ) > [-1] 5 minute fast stochastic %d( 233 , 3 ) * 1.02 ) > 35 and [ -1 ] 5 minute count( 75, 1 where [0] 5 minute fast stochastic %d( 233 , 3 ) > [ -2 ] 5 minute fast stochastic %d( 233 , 3 ) * 1.02 ) <= 35 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | [0] 15 minute max( 144 ,  [0] 15 minute fast stochastic %d( 233 ,  3 ) ) - [0] 15 minute min( 144 ,  [0] 15 minute fast stochastic %d( 233 ,  3 ) ) crossed above 89 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Stochastic compares close location within a high-low range over its lookback. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 3 | Enabled | [GROUP segment=cash join=any combination=passes measurevalue=default] | Nested group over segment **cash** with join **any** (combination=passes). Group status=Enabled. |
| 4 | Enabled | [0] 15 minute fast stochastic %d( 233 ,  3 ) > [-144] 15 minute fast stochastic %d( 233 ,  3 ) | Inequality test: left expression must be strictly greater than right. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | Enabled | [0] 15 minute fast stochastic %d( 233 ,  3 ) < [-144] 15 minute fast stochastic %d( 233 ,  3 ) | Inequality test: left expression must be strictly less than right. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 7 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 8 | Enabled | [-144] 15 minute count( 610, 1 where [0] 15 minute fast stochastic %d( 233 ,  3 ) < 60 ) > 550 | Inequality test: left expression must be strictly greater than right. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | Enabled | [0] 15 minute count( 144, 1 where [0] 15 minute fast stochastic %d( 233 ,  3 ) > 60 ) crossed above 120 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 11 | Enabled | [0] 5 minute count( 75, 1 where [0] 5 minute fast stochastic %d( 233 ,  3 ) > [-1] 5 minute fast stochastic %d( 233 ,  3 ) * 1.02 ) crossed above 35 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[0] 15 minute max( 144 ,  [0] 15 minute fast stochastic %d( 233 ,  3 ) ) - [0] 15 minute min( 144 ,  [0] 15 minute fast stochastic %d( 233 ,  3 ) ) crossed above 89` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Stochastic compares close location within a high-low range over its lookback. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#4** `[0] 15 minute fast stochastic %d( 233 ,  3 ) > [-144] 15 minute fast stochastic %d( 233 ,  3 )` — Inequality test: left expression must be strictly greater than right. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[0] 15 minute fast stochastic %d( 233 ,  3 ) < [-144] 15 minute fast stochastic %d( 233 ,  3 )` — Inequality test: left expression must be strictly less than right. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[-144] 15 minute count( 610, 1 where [0] 15 minute fast stochastic %d( 233 ,  3 ) < 60 ) > 550` — Inequality test: left expression must be strictly greater than right. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[0] 15 minute count( 144, 1 where [0] 15 minute fast stochastic %d( 233 ,  3 ) > 60 ) crossed above 120` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#11** `[0] 5 minute count( 75, 1 where [0] 5 minute fast stochastic %d( 233 ,  3 ) > [-1] 5 minute fast stochastic %d( 233 ,  3 ) * 1.02 ) crossed above 35` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `fast stochastic %d` — appears 10 time(s) in the expression tree
- `count` — appears 3 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 4 occurrence(s)
- `crossed above` — 3 occurrence(s)
- `<` — 2 occurrence(s)
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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `15_minute`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Breakout, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Oscillator, Breakout, Momentum, Multi-factor
- **Tags:** universe:nifty-200, indicator:stochastic, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

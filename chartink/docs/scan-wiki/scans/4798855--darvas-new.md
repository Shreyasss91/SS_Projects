---
scan_id: 4798855
scan_name: darvas new
source_url: https://chartink.com/screener/darvas-new-2
market: Indian equities
horizon: Intraday
classification: ["Oscillator", "Moving average", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:cash", "indicator:rsi", "indicator:volume", "indicator:sma", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Oscillator
---

# darvas new

## Source

- Chartink URL: https://chartink.com/screener/darvas-new-2
- Scan ID: `4798855`
- Slug: `darvas-new-2`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2021-06-04T02:25:33.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4798855.json](../source-snapshots/4798855.json)
- Text snapshot: [source-snapshots/4798855.txt](../source-snapshots/4798855.txt)

## What this scan is for

This scan, titled "darvas new", appears designed to screen Indian equities in the **cash** universe using **6 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Oscillator, Moving average, Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 30_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: darvas new
Scan id: 4798855
Slug: darvas-new-2
Source URL: https://chartink.com/screener/darvas-new-2
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-04T02:25:33.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close * 1 day ago volume > 100000000
2. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Enabled] ( [0] 30 minute high - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) * 100 / ( [0] 30 minute max( 120 ,  [0] 30 minute high ) - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) crossed above 97
    group_path: root/group[cash|all]
4. [Disabled] [-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.1
    group_path: root/group[cash|all]
5. [Enabled] [-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.05
    group_path: root/group[cash|all]
6. [Enabled] [0] 30 minute sma( close ,  5 ) > [-6] 30 minute sma( close ,  5 )
    group_path: root/group[cash|all]
7. [Disabled] daily rsi( 14 ) > 60
    group_path: root/group[cash|all]
8. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
9. [Enabled] ( [0] 30 minute high - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) * 100 / ( [0] 30 minute max( 120 ,  [0] 30 minute high ) - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) crossed below 10
    group_path: root/group[cash|all]
10. [Enabled] [-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.1
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( cash ( 1 day ago close * 1 day ago volume > 100000000 and( cash ( ( [0] 30 minute high - [0] 30 minute min( 120 , [0] 30 minute low ) ) * 100 / ( [0] 30 minute max( 120 , [0] 30 minute high ) - [0] 30 minute min( 120 , [0] 30 minute low ) ) > 97 and( [ -1 ] 30 minute high - [ -1 ] 30 minute min( 120 , [0] 30 minute low )) * 100 / ( [ -1 ] 30 minute max( 120 , [0] 30 minute high )- [ -1 ] 30 minute min( 120 , [0] 30 minute low )) <= 97 and [-4] 30 minute max( 120 , [0] 30 minute high ) < [-4] 30 minute min( 120 , [0] 30 minute low ) * 1.05 and [0] 30 minute sma( [-1] 30 minute volume , 5 ) > [-6] 30 minute sma( [-1] 30 minute volume , 5 ) ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 3 | Enabled | ( [0] 30 minute high - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) * 100 / ( [0] 30 minute max( 120 ,  [0] 30 minute high ) - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) crossed above 97 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | Disabled | [-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.1 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | Enabled | [-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.05 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | Enabled | [0] 30 minute sma( close ,  5 ) > [-6] 30 minute sma( close ,  5 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | Disabled | daily rsi( 14 ) > 60 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 8 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 9 | Enabled | ( [0] 30 minute high - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) * 100 / ( [0] 30 minute max( 120 ,  [0] 30 minute high ) - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) crossed below 10 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | Enabled | [-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.1 | Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `( [0] 30 minute high - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) * 100 / ( [0] 30 minute max( 120 ,  [0] 30 minute high ) - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) crossed above 97` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.05` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[0] 30 minute sma( close ,  5 ) > [-6] 30 minute sma( close ,  5 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `( [0] 30 minute high - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) * 100 / ( [0] 30 minute max( 120 ,  [0] 30 minute high ) - [0] 30 minute min( 120 ,  [0] 30 minute low ) ) crossed below 10` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.1` — Inequality test: left expression must be strictly less than right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #4
- **Condition (verbatim):** `[-4] 30 minute max( 120 ,  [0] 30 minute high ) < [-4] 30 minute min( 120 ,  [0] 30 minute low ) * 1.1`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `daily rsi( 14 ) > 60`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `min` — appears 7 time(s) in the expression tree
- `low` — appears 7 time(s) in the expression tree
- `high` — appears 7 time(s) in the expression tree
- `max` — appears 5 time(s) in the expression tree
- `volume` — appears 3 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `rsi` — appears 1 time(s) in the expression tree

### Operators observed
- `*` — 6 occurrence(s)
- `>` — 3 occurrence(s)
- `<` — 3 occurrence(s)
- `/` — 2 occurrence(s)
- `crossed above` — 1 occurrence(s)
- `crossed below` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `30_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Oscillator, Moving average, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:cash, indicator:rsi, indicator:volume, indicator:sma, timeframe:intraday-bars, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

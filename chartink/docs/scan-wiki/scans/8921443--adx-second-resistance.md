---
scan_id: 8921443
scan_name: adx second resistance
source_url: https://chartink.com/screener/adx-second-resistance
market: Indian equities
horizon: Multi-horizon
classification: ["Oscillator", "Support/resistance", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:nifty-50", "indicator:adx", "timeframe:intraday-bars", "timeframe:weekly", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 4
needs_review_filter_count: 0
root_segment: nifty 500
root_join: any
primary_classification: Oscillator
---

# adx second resistance

## Source

- Chartink URL: https://chartink.com/screener/adx-second-resistance
- Scan ID: `8921443`
- Slug: `adx-second-resistance`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2022-07-01T17:08:46.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8921443.json](../source-snapshots/8921443.json)
- Text snapshot: [source-snapshots/8921443.txt](../source-snapshots/8921443.txt)

## What this scan is for

This scan, titled "adx second resistance", appears designed to screen Indian equities in the **nifty 500** universe using **1 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Oscillator, Support/resistance, Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Multi-horizon**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 0_weeks_ago, 120_minute, 1_days_ago, 1_weeks_ago, 60_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: adx second resistance
Scan id: 8921443
Slug: adx-second-resistance
Source URL: https://chartink.com/screener/adx-second-resistance
Root universe/segment: nifty 500
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-07-01T17:08:46.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=nifty 500 join=all combination=passes measurevalue=default]  (path: root/group[nifty 500|all])
2. [Enabled] 1 day ago adx di positive( 14 ) + ( 1 day ago max( 21 ,  daily adx di positive( 14 ) ) - 1 day ago min( 21 ,  daily adx di positive( 14 ) ) ) crossed below daily adx di positive( 14 )
    group_path: root/group[nifty 500|all]
3. [Disabled] 1 week ago adx di positive( 14 ) + ( 1 week ago max( 21 ,  1 week ago adx di positive( 14 ) ) - 1 week ago min( 21 ,  1 week ago adx di positive( 14 ) ) ) crossed below weekly adx di positive( 14 )
    group_path: root/group[nifty 500|all]
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Disabled] daily high > 1 day ago max( 21 ,  daily high )
    group_path: root/group[cash|all]
6. [Disabled] [-1] 60 minute accdist + ( [-1] 60 minute max( 28 ,  [0] 60 minute accdist ) - [-1] 60 minute min( 28 ,  [0] 60 minute accdist ) ) crossed above [0] 60 minute accdist
    group_path: root/group[cash|all]
7. [Disabled] [-1] 120 minute accdist + ( [-1] 120 minute max( 21 ,  [0] 120 minute accdist ) - [-1] 120 minute min( 21 ,  [0] 120 minute accdist ) ) crossed above [0] 120 minute accdist
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 500 ( ( nifty 500 ( 1 day ago adx di positive( 14 ) + ( 1 day ago max( 21 , latest adx di positive( 14 ) ) - 1 day ago min( 21 , latest adx di positive( 14 ) ) ) < latest adx di positive( 14 ) and 2 day ago  adx di positive( 14 ) + ( 2 day ago  max( 21 , latest adx di positive( 14 ) )- 2 day ago  min( 21 , latest adx di positive( 14 ) )) >= 1 day ago  adx di positive( 14 ) ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=nifty 500 join=all combination=passes measurevalue=default] | Nested group over segment **nifty 500** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | 1 day ago adx di positive( 14 ) + ( 1 day ago max( 21 ,  daily adx di positive( 14 ) ) - 1 day ago min( 21 ,  daily adx di positive( 14 ) ) ) crossed below daily adx di positive( 14 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 3 | Disabled | 1 week ago adx di positive( 14 ) + ( 1 week ago max( 21 ,  1 week ago adx di positive( 14 ) ) - 1 week ago min( 21 ,  1 week ago adx di positive( 14 ) ) ) crossed below weekly adx di positive( 14 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 4 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 5 | Disabled | daily high > 1 day ago max( 21 ,  daily high ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 6 | Disabled | [-1] 60 minute accdist + ( [-1] 60 minute max( 28 ,  [0] 60 minute accdist ) - [-1] 60 minute min( 28 ,  [0] 60 minute accdist ) ) crossed above [0] 60 minute accdist | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | Disabled | [-1] 120 minute accdist + ( [-1] 120 minute max( 21 ,  [0] 120 minute accdist ) - [-1] 120 minute min( 21 ,  [0] 120 minute accdist ) ) crossed above [0] 120 minute accdist | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago adx di positive( 14 ) + ( 1 day ago max( 21 ,  daily adx di positive( 14 ) ) - 1 day ago min( 21 ,  daily adx di positive( 14 ) ) ) crossed below daily adx di positive( 14 )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **4** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `1 week ago adx di positive( 14 ) + ( 1 week ago max( 21 ,  1 week ago adx di positive( 14 ) ) - 1 week ago min( 21 ,  1 week ago adx di positive( 14 ) ) ) crossed below weekly adx di positive( 14 )`
- **Meaning:** Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily high > 1 day ago max( 21 ,  daily high )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `[-1] 60 minute accdist + ( [-1] 60 minute max( 28 ,  [0] 60 minute accdist ) - [-1] 60 minute min( 28 ,  [0] 60 minute accdist ) ) crossed above [0] 60 minute accdist`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `[-1] 120 minute accdist + ( [-1] 120 minute max( 21 ,  [0] 120 minute accdist ) - [-1] 120 minute min( 21 ,  [0] 120 minute accdist ) ) crossed above [0] 120 minute accdist`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `adx di positive` — appears 8 time(s) in the expression tree
- `accdist` — appears 8 time(s) in the expression tree
- `max` — appears 5 time(s) in the expression tree
- `min` — appears 4 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree

### Operators observed
- `+` — 4 occurrence(s)
- `crossed below` — 2 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `>` — 1 occurrence(s)

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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `120_minute`, `1_days_ago`, `1_weeks_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Support/resistance, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **4** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Oscillator, Support/resistance, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:nifty-50, indicator:adx, timeframe:intraday-bars, timeframe:weekly, timeframe:daily
- **Root universe:** nifty 500
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

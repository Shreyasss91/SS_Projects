---
scan_id: 11391333
scan_name: STRONG PRICE REJECTIONS_index_test
source_url: https://chartink.com/screener/strong-price-rejections-index-test
market: Indian equities
horizon: Intraday
classification: ["Momentum"]
tags: ["universe:index", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 6
needs_review_filter_count: 0
root_segment: NIFTY_INDEX
root_join: any
primary_classification: Momentum
---

# STRONG PRICE REJECTIONS_index_test

## Source

- Chartink URL: https://chartink.com/screener/strong-price-rejections-index-test
- Scan ID: `11391333`
- Slug: `strong-price-rejections-index-test`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-04-01T02:56:16.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11391333.json](../source-snapshots/11391333.json)
- Text snapshot: [source-snapshots/11391333.txt](../source-snapshots/11391333.txt)

## What this scan is for

This scan, titled "STRONG PRICE REJECTIONS_index_test", appears designed to screen Indian equities in the **NIFTY_INDEX** universe using **5 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Momentum**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 30_minute, 5_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: STRONG PRICE REJECTIONS_index_test
Scan id: 11391333
Slug: strong-price-rejections-index-test
Source URL: https://chartink.com/screener/strong-price-rejections-index-test
Root universe/segment: NIFTY_INDEX
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-01T02:56:16.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily high - daily greatest > 125
    group_path: root/group[cash|all]
3. [Disabled] daily low - daily least < -125
    group_path: root/group[cash|all]
4. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Disabled] daily high - daily greatest = daily max( 30 ,  daily high - daily greatest )
    group_path: root/group[cash|all]
6. [Disabled] daily low - daily least = daily min( 30 ,  daily low - daily least )
    group_path: root/group[cash|all]
7. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Enabled] 1 day ago high - daily greatest > 90
    group_path: root/group[cash|all]
9. [Enabled] daily open < 1 day ago high
    group_path: root/group[cash|all]
10. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
11. [Disabled] daily abs( [0] 30 minute close - [0] 30 minute open ) = [0] 30 minute max( 200 ,  [0] 30 minute abs( [0] 30 minute close - [0] 30 minute open ) )
    group_path: root/group[cash|all]
12. [Enabled] daily abs( [0] 30 minute close - [0] 30 minute open ) > 50
    group_path: root/group[cash|all]
13. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Disabled] daily abs( [0] 30 minute close - [0] 30 minute open ) = [0] 30 minute max( 200 ,  [0] 30 minute abs( [0] 30 minute close - [0] 30 minute open ) )
    group_path: root/group[cash|all]
15. [Disabled] daily abs( [0] 30 minute close - [0] 30 minute open ) > 50
    group_path: root/group[cash|all]
16. [Enabled] daily abs( [0] 5 minute max( 15 ,  [0] 5 minute high ) - [0] 5 minute min( 15 ,  [0] 5 minute low ) ) crossed above 80
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty_index ( ( cash ( abs( [0] 5 minute max( 15 , [0] 5 minute high ) - [0] 5 minute min( 15 , [0] 5 minute low ) ) > 80 and abs( [ -1 ] 5 minute max( 15 , [0] 5 minute high )- [ -1 ] 5 minute min( 15 , [0] 5 minute low )) <= 80 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 2 | Enabled | daily high - daily greatest > 125 | Inequality test: left expression must be strictly greater than right. |
| 3 | Disabled | daily low - daily least < -125 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 4 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 5 | Disabled | daily high - daily greatest = daily max( 30 ,  daily high - daily greatest ) | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 6 | Disabled | daily low - daily least = daily min( 30 ,  daily low - daily least ) | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. |
| 7 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 8 | Enabled | 1 day ago high - daily greatest > 90 | Inequality test: left expression must be strictly greater than right. |
| 9 | Enabled | daily open < 1 day ago high | Inequality test: left expression must be strictly less than right. |
| 10 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 11 | Disabled | daily abs( [0] 30 minute close - [0] 30 minute open ) = [0] 30 minute max( 200 ,  [0] 30 minute abs( [0] 30 minute close - [0] 30 minute open ) ) | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 12 | Enabled | daily abs( [0] 30 minute close - [0] 30 minute open ) > 50 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 13 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 14 | Disabled | daily abs( [0] 30 minute close - [0] 30 minute open ) = [0] 30 minute max( 200 ,  [0] 30 minute abs( [0] 30 minute close - [0] 30 minute open ) ) | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 15 | Disabled | daily abs( [0] 30 minute close - [0] 30 minute open ) > 50 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 16 | Enabled | daily abs( [0] 5 minute max( 15 ,  [0] 5 minute high ) - [0] 5 minute min( 15 ,  [0] 5 minute low ) ) crossed above 80 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily high - daily greatest > 125` — Inequality test: left expression must be strictly greater than right.
- **#8** `1 day ago high - daily greatest > 90` — Inequality test: left expression must be strictly greater than right.
- **#9** `daily open < 1 day ago high` — Inequality test: left expression must be strictly less than right.
- **#12** `daily abs( [0] 30 minute close - [0] 30 minute open ) > 50` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#16** `daily abs( [0] 5 minute max( 15 ,  [0] 5 minute high ) - [0] 5 minute min( 15 ,  [0] 5 minute low ) ) crossed above 80` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **6** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily low - daily least < -125`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily high - daily greatest = daily max( 30 ,  daily high - daily greatest )`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `daily low - daily least = daily min( 30 ,  daily low - daily least )`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `daily abs( [0] 30 minute close - [0] 30 minute open ) = [0] 30 minute max( 200 ,  [0] 30 minute abs( [0] 30 minute close - [0] 30 minute open ) )`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `daily abs( [0] 30 minute close - [0] 30 minute open ) = [0] 30 minute max( 200 ,  [0] 30 minute abs( [0] 30 minute close - [0] 30 minute open ) )`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #15
- **Condition (verbatim):** `daily abs( [0] 30 minute close - [0] 30 minute open ) > 50`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `open` — appears 14 time(s) in the expression tree
- `close` — appears 13 time(s) in the expression tree
- `abs` — appears 7 time(s) in the expression tree
- `high` — appears 6 time(s) in the expression tree
- `greatest` — appears 4 time(s) in the expression tree
- `low` — appears 4 time(s) in the expression tree
- `max` — appears 4 time(s) in the expression tree
- `least` — appears 3 time(s) in the expression tree
- `min` — appears 2 time(s) in the expression tree

### Operators observed
- `-` — 5 occurrence(s)
- `>` — 4 occurrence(s)
- `=` — 4 occurrence(s)
- `<` — 2 occurrence(s)
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
- Universe/segment: **NIFTY_INDEX**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `30_minute`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **NIFTY_INDEX**. Liquidity and index membership still vary inside that set.
- **Method context:** Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **5** active filters — transparent screening logic.
- Universe pinned to **NIFTY_INDEX**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **6** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Momentum
- **Tags:** universe:index, timeframe:intraday-bars, timeframe:daily
- **Root universe:** NIFTY_INDEX
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

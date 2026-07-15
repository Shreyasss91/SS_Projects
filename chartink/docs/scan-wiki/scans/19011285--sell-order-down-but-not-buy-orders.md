---
scan_id: 19011285
scan_name: sell order down but not buy orders
source_url: https://chartink.com/screener/sell-order-down-but-not-buy-orders
market: Indian equities
horizon: Swing
classification: ["Support/resistance", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["short-bias", "long-bias", "universe:midcap", "indicator:pivot", "timeframe:weekly", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 12
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty midcap 150
root_join: all
primary_classification: Support/resistance
---

# sell order down but not buy orders

## Source

- Chartink URL: https://chartink.com/screener/sell-order-down-but-not-buy-orders
- Scan ID: `19011285`
- Slug: `sell-order-down-but-not-buy-orders`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2024-10-15T07:18:27.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/19011285.json](../source-snapshots/19011285.json)
- Text snapshot: [source-snapshots/19011285.txt](../source-snapshots/19011285.txt)

## What this scan is for

This scan, titled "sell order down but not buy orders", appears designed to screen Indian equities in the **nifty midcap 150** universe using **12 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Support/resistance, Volume/delivery, Momentum, Multi-factor**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 0_weeks_ago, 1_days_ago, 2_days_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: sell order down but not buy orders
Scan id: 19011285
Slug: sell-order-down-but-not-buy-orders
Source URL: https://chartink.com/screener/sell-order-down-but-not-buy-orders
Root universe/segment: nifty midcap 150
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2024-10-15T07:18:27.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily sell orders quantity < 1 day ago sell orders quantity * 0.5
    group_path: root/group[cash|all]
3. [Enabled] 1 day ago sell orders quantity > 2 days ago sell orders quantity * 1
    group_path: root/group[cash|all]
4. [Disabled] daily buy orders quantity > 1 day ago buy orders quantity * 1
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] daily sell orders quantity crossed below 1 day ago min( 10 ,  daily sell orders quantity )
    group_path: root/group[cash|all]
7. [Enabled] daily buy orders quantity > 1 day ago min( 10 ,  daily buy orders quantity )
    group_path: root/group[cash|all]
8. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
9. [Enabled] daily buy orders quantity crossed below 1 day ago min( 10 ,  daily buy orders quantity )
    group_path: root/group[cash|all]
10. [Enabled] daily sell orders quantity > 1 day ago min( 10 ,  daily sell orders quantity )
    group_path: root/group[cash|all]
11. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
12. [Enabled] daily abs( 1 - ( daily close / weekly pivot point s1 ) ) <= 0.01
    group_path: root/group[cash|any]
13. [Enabled] daily abs( 1 - ( daily close / weekly pivot point s2 ) ) <= 0.01
    group_path: root/group[cash|any]
14. [Enabled] daily abs( 1 - ( daily close / weekly pivot point ) ) <= 0.01
    group_path: root/group[cash|any]
15. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
16. [Enabled] daily abs( 1 - ( daily close / weekly pivot point r1 ) ) <= 0.01
    group_path: root/group[cash|any]
17. [Enabled] daily abs( 1 - ( daily close / weekly pivot point r2 ) ) <= 0.01
    group_path: root/group[cash|any]
18. [Disabled] daily abs( 1 - ( daily close / weekly pivot point ) ) <= 0.01
    group_path: root/group[cash|any]
19. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
20. [Enabled] daily buy orders quantity ratio > 20
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty midcap 150 ( ( cash ( latest "buy orders quantity / sell orders quantity" > 20 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 2 | Enabled | daily sell orders quantity < 1 day ago sell orders quantity * 0.5 | Inequality test: left expression must be strictly less than right. |
| 3 | Enabled | 1 day ago sell orders quantity > 2 days ago sell orders quantity * 1 | Inequality test: left expression must be strictly greater than right. |
| 4 | Disabled | daily buy orders quantity > 1 day ago buy orders quantity * 1 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 5 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 6 | Enabled | daily sell orders quantity crossed below 1 day ago min( 10 ,  daily sell orders quantity ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 7 | Enabled | daily buy orders quantity > 1 day ago min( 10 ,  daily buy orders quantity ) | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |
| 8 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 9 | Enabled | daily buy orders quantity crossed below 1 day ago min( 10 ,  daily buy orders quantity ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 10 | Enabled | daily sell orders quantity > 1 day ago min( 10 ,  daily sell orders quantity ) | Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars. |
| 11 | Disabled | [GROUP segment=cash join=any combination=passes measurevalue=default] | Nested group over segment **cash** with join **any** (combination=passes). Group status=Disabled. |
| 12 | Enabled | daily abs( 1 - ( daily close / weekly pivot point s1 ) ) <= 0.01 | Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset. |
| 13 | Enabled | daily abs( 1 - ( daily close / weekly pivot point s2 ) ) <= 0.01 | Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset. |
| 14 | Enabled | daily abs( 1 - ( daily close / weekly pivot point ) ) <= 0.01 | Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset. |
| 15 | Disabled | [GROUP segment=cash join=any combination=passes measurevalue=default] | Nested group over segment **cash** with join **any** (combination=passes). Group status=Disabled. |
| 16 | Enabled | daily abs( 1 - ( daily close / weekly pivot point r1 ) ) <= 0.01 | Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset. |
| 17 | Enabled | daily abs( 1 - ( daily close / weekly pivot point r2 ) ) <= 0.01 | Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset. |
| 18 | Disabled | daily abs( 1 - ( daily close / weekly pivot point ) ) <= 0.01 | Inequality test: left expression must be less than or equal to right. Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset. |
| 19 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 20 | Enabled | daily buy orders quantity ratio > 20 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **12** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily sell orders quantity < 1 day ago sell orders quantity * 0.5` — Inequality test: left expression must be strictly less than right.
- **#3** `1 day ago sell orders quantity > 2 days ago sell orders quantity * 1` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily sell orders quantity crossed below 1 day ago min( 10 ,  daily sell orders quantity )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#7** `daily buy orders quantity > 1 day ago min( 10 ,  daily buy orders quantity )` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.
- **#9** `daily buy orders quantity crossed below 1 day ago min( 10 ,  daily buy orders quantity )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars.
- **#10** `daily sell orders quantity > 1 day ago min( 10 ,  daily sell orders quantity )` — Inequality test: left expression must be strictly greater than right. min(N, series) is the lowest value of series over N bars.
- **#12** `daily abs( 1 - ( daily close / weekly pivot point s1 ) ) <= 0.01` — Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset.
- **#13** `daily abs( 1 - ( daily close / weekly pivot point s2 ) ) <= 0.01` — Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset.
- **#14** `daily abs( 1 - ( daily close / weekly pivot point ) ) <= 0.01` — Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset.
- **#16** `daily abs( 1 - ( daily close / weekly pivot point r1 ) ) <= 0.01` — Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset.
- **#17** `daily abs( 1 - ( daily close / weekly pivot point r2 ) ) <= 0.01` — Inequality test: left expression must be less than or equal to right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset.
- **#20** `daily buy orders quantity ratio > 20` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #4
- **Condition (verbatim):** `daily buy orders quantity > 1 day ago buy orders quantity * 1`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #18
- **Condition (verbatim):** `daily abs( 1 - ( daily close / weekly pivot point ) ) <= 0.01`
- **Meaning:** Inequality test: left expression must be less than or equal to right. Currently disabled in source — not applied when the scan runs. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. References weekly bars / weekly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `sell orders quantity` — appears 8 time(s) in the expression tree
- `buy orders quantity` — appears 6 time(s) in the expression tree
- `abs` — appears 6 time(s) in the expression tree
- `close` — appears 6 time(s) in the expression tree
- `min` — appears 4 time(s) in the expression tree
- `pivot point` — appears 2 time(s) in the expression tree
- `pivot point s1` — appears 1 time(s) in the expression tree
- `pivot point s2` — appears 1 time(s) in the expression tree
- `pivot point r1` — appears 1 time(s) in the expression tree
- `pivot point r2` — appears 1 time(s) in the expression tree
- `buy orders quantity ratio` — appears 1 time(s) in the expression tree

### Operators observed
- `<=` — 6 occurrence(s)
- `>` — 5 occurrence(s)
- `*` — 3 occurrence(s)
- `crossed below` — 2 occurrence(s)
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
- Universe/segment: **nifty midcap 150**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `1_days_ago`, `2_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty midcap 150**. Liquidity and index membership still vary inside that set.
- **Method context:** Support/resistance, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **12** active filters — transparent screening logic.
- Universe pinned to **nifty midcap 150**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Support/resistance, Volume/delivery, Momentum, Multi-factor
- **Tags:** short-bias, long-bias, universe:midcap, indicator:pivot, timeframe:weekly, timeframe:daily
- **Root universe:** nifty midcap 150
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

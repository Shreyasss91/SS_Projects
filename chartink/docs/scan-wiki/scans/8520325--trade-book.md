---
scan_id: 8520325
scan_name: trade book
source_url: https://chartink.com/screener/trade-book-8
market: Indian equities
horizon: Intraday
classification: ["Fundamental", "Moving average", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:cash", "indicator:vwap", "indicator:volume", "indicator:sma", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 7
disabled_filter_count: 10
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Fundamental
---

# trade book

## Source

- Chartink URL: https://chartink.com/screener/trade-book-8
- Scan ID: `8520325`
- Slug: `trade-book-8`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2022-05-06T12:58:46.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8520325.json](../source-snapshots/8520325.json)
- Text snapshot: [source-snapshots/8520325.txt](../source-snapshots/8520325.txt)

## What this scan is for

This scan, titled "trade book", appears designed to screen Indian equities in the **cash** universe using **7 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Fundamental, Moving average, Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 14_days_ago, 30_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: trade book
Scan id: 8520325
Slug: trade-book-8
Source URL: https://chartink.com/screener/trade-book-8
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-05-06T12:58:46.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
    group_path: root/group[cash|all]
3. [Disabled] daily market cap > 2000
    group_path: root/group[cash|all]
4. [Disabled] daily market cap > 10000
    group_path: root/group[cash|all]
5. [Enabled] daily close * daily volume > 20000000
    group_path: root/group[cash|all]
6. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Disabled] [0] 30 minute close < [-6] 30 minute close * 0.97
    group_path: root/group[cash|all]
8. [Enabled] daily buyer initiated trades ratio > 2
    group_path: root/group[cash|all]
9. [Enabled] daily buyer initiated trades quantity ratio > 2
    group_path: root/group[cash|all]
10. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
11. [Enabled] daily buyer initiated trades avg quantity > daily seller initiated trades avg quantity
    group_path: root/group[cash|all]
12. [Enabled] daily buy trades vwap > daily sell trades vwap
    group_path: root/group[cash|all]
13. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
14. [Disabled] daily cancelled sell orders quantity / daily sell orders quantity > 100
    group_path: root/group[cash|all]
15. [Disabled] daily cancelled sell orders quantity / daily orders quantity > 20
    group_path: root/group[cash|all]
16. [Disabled] daily cancelled buy orders quantity:  / daily orders quantity > 20
    group_path: root/group[cash|all]
17. [Disabled] daily cancelled buy orders quantity:  / daily buy orders quantity > 10
    group_path: root/group[cash|all]
18. [Disabled] daily buyer initiated trades quantity ratio > 1
    group_path: root/group[cash|all]
19. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
20. [Disabled] daily sma( close ,  14 ) / 14 days ago sma( close ,  14 ) crossed above 2
    group_path: root/group[cash|all]
21. [Disabled] daily sma( close ,  20 ) crossed above daily sma( close ,  20 )
    group_path: root/group[cash|all]
22. [Enabled] daily buyer initiated trades quantity / daily volume > 0.8
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( cash ( ( cash ( latest count( 200, 1 where( latest high / latest low ) = 1 ) < 1 and latest close * latest volume > 20000000 ) ) and( cash ( latest buyer initiated trades quantity / latest volume > 0.8 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1 | Inequality test: left expression must be strictly less than right. |
| 3 | Disabled | daily market cap > 2000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Filters by market-capitalisation field from Chartink fundamentals. |
| 4 | Disabled | daily market cap > 10000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Filters by market-capitalisation field from Chartink fundamentals. |
| 5 | Enabled | daily close * daily volume > 20000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 6 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 7 | Disabled | [0] 30 minute close < [-6] 30 minute close * 0.97 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | Enabled | daily buyer initiated trades ratio > 2 | Inequality test: left expression must be strictly greater than right. |
| 9 | Enabled | daily buyer initiated trades quantity ratio > 2 | Inequality test: left expression must be strictly greater than right. |
| 10 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 11 | Enabled | daily buyer initiated trades avg quantity > daily seller initiated trades avg quantity | Inequality test: left expression must be strictly greater than right. |
| 12 | Enabled | daily buy trades vwap > daily sell trades vwap | Inequality test: left expression must be strictly greater than right. VWAP is volume-weighted average price for the session/period context Chartink supplies. |
| 13 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 14 | Disabled | daily cancelled sell orders quantity / daily sell orders quantity > 100 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 15 | Disabled | daily cancelled sell orders quantity / daily orders quantity > 20 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 16 | Disabled | daily cancelled buy orders quantity:  / daily orders quantity > 20 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 17 | Disabled | daily cancelled buy orders quantity:  / daily buy orders quantity > 10 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 18 | Disabled | daily buyer initiated trades quantity ratio > 1 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 19 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 20 | Disabled | daily sma( close ,  14 ) / 14 days ago sma( close ,  14 ) crossed above 2 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. |
| 21 | Disabled | daily sma( close ,  20 ) crossed above daily sma( close ,  20 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. |
| 22 | Enabled | daily buyer initiated trades quantity / daily volume > 0.8 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **7** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1` — Inequality test: left expression must be strictly less than right.
- **#5** `daily close * daily volume > 20000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#8** `daily buyer initiated trades ratio > 2` — Inequality test: left expression must be strictly greater than right.
- **#9** `daily buyer initiated trades quantity ratio > 2` — Inequality test: left expression must be strictly greater than right.
- **#11** `daily buyer initiated trades avg quantity > daily seller initiated trades avg quantity` — Inequality test: left expression must be strictly greater than right.
- **#12** `daily buy trades vwap > daily sell trades vwap` — Inequality test: left expression must be strictly greater than right. VWAP is volume-weighted average price for the session/period context Chartink supplies.
- **#22** `daily buyer initiated trades quantity / daily volume > 0.8` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **10** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily market cap > 2000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Filters by market-capitalisation field from Chartink fundamentals.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `daily market cap > 10000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Filters by market-capitalisation field from Chartink fundamentals.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #7
- **Condition (verbatim):** `[0] 30 minute close < [-6] 30 minute close * 0.97`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #14
- **Condition (verbatim):** `daily cancelled sell orders quantity / daily sell orders quantity > 100`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #15
- **Condition (verbatim):** `daily cancelled sell orders quantity / daily orders quantity > 20`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `daily cancelled buy orders quantity:  / daily orders quantity > 20`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #17
- **Condition (verbatim):** `daily cancelled buy orders quantity:  / daily buy orders quantity > 10`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #18
- **Condition (verbatim):** `daily buyer initiated trades quantity ratio > 1`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #20
- **Condition (verbatim):** `daily sma( close ,  14 ) / 14 days ago sma( close ,  14 ) crossed above 2`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #21
- **Condition (verbatim):** `daily sma( close ,  20 ) crossed above daily sma( close ,  20 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `buy orders quantity` — appears 4 time(s) in the expression tree
- `sma` — appears 4 time(s) in the expression tree
- `close` — appears 3 time(s) in the expression tree
- `buyer initiated trades quantity` — appears 3 time(s) in the expression tree
- `market cap` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `buyer initiated trades quantity ratio` — appears 2 time(s) in the expression tree
- `cancelled sell orders quantity` — appears 2 time(s) in the expression tree
- `sell orders quantity` — appears 2 time(s) in the expression tree
- `orders quantity` — appears 2 time(s) in the expression tree
- `cancelled buy orders quantity: ` — appears 2 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `buyer initiated trades ratio` — appears 1 time(s) in the expression tree
- `buyer initiated trades avg quantity` — appears 1 time(s) in the expression tree
- `seller initiated trades avg quantity` — appears 1 time(s) in the expression tree
- `buy trades vwap` — appears 1 time(s) in the expression tree
- `sell trades vwap` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 13 occurrence(s)
- `/` — 6 occurrence(s)
- `<` — 2 occurrence(s)
- `*` — 2 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `=` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `14_days_ago`, `30_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **7** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **10** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Fundamental, Moving average, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:cash, indicator:vwap, indicator:volume, indicator:sma, timeframe:intraday-bars, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

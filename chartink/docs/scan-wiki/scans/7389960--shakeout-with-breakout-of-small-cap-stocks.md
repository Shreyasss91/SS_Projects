---
scan_id: 7389960
scan_name: Shakeout with Breakout of small cap stocks
source_url: https://chartink.com/screener/shakeout-with-breakout-of-small-cap-stocks
market: Indian equities
horizon: Swing
classification: ["Breakout", "Moving average", "Fundamental", "Multi-factor"]
tags: ["universe:cash", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: any
primary_classification: Breakout
---

# Shakeout with Breakout of small cap stocks

## Source

- Chartink URL: https://chartink.com/screener/shakeout-with-breakout-of-small-cap-stocks
- Scan ID: `7389960`
- Slug: `shakeout-with-breakout-of-small-cap-stocks`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2022-01-05T12:05:04.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/7389960.json](../source-snapshots/7389960.json)
- Text snapshot: [source-snapshots/7389960.txt](../source-snapshots/7389960.txt)

## What this scan is for

This scan, titled "Shakeout with Breakout of small cap stocks", appears designed to screen Indian equities in the **cash** universe using **8 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Breakout, Moving average, Fundamental, Multi-factor**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago`.

Author description (source metadata): MCAP between 1000 to 10000 crores

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Shakeout with Breakout of small cap stocks
Scan id: 7389960
Slug: shakeout-with-breakout-of-small-cap-stocks
Source URL: https://chartink.com/screener/shakeout-with-breakout-of-small-cap-stocks
Root universe/segment: cash
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-01-05T12:05:04.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily low < daily least * 0.95
    group_path: root/group[cash|all]
3. [Enabled] daily market cap > 1000
    group_path: root/group[cash|all]
4. [Enabled] daily market cap < 10000
    group_path: root/group[cash|all]
5. [Enabled] daily high = daily max( 90 ,  daily high )
    group_path: root/group[cash|all]
6. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
7. [Enabled] daily high > daily greatest * 1.05
    group_path: root/group[cash|all]
8. [Enabled] daily market cap > 1000
    group_path: root/group[cash|all]
9. [Enabled] daily market cap < 10000
    group_path: root/group[cash|all]
10. [Enabled] daily high = daily max( 90 ,  daily high )
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( cash ( ( cash ( latest low < least(  latest open, latest close  ) * 0.95 and market cap > 1000 and market cap < 10000 and latest high = latest max( 90 , latest high ) ) ) or( cash ( latest high > greatest(  latest open, latest close  ) * 1.05 and market cap > 1000 and market cap < 10000 and latest high = latest max( 90 , latest high ) ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | daily low < daily least * 0.95 | Inequality test: left expression must be strictly less than right. |
| 3 | Enabled | daily market cap > 1000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 4 | Enabled | daily market cap < 10000 | Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 5 | Enabled | daily high = daily max( 90 ,  daily high ) | Equality test between left and right expressions. max(N, series) is the highest value of series over N bars. |
| 6 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 7 | Enabled | daily high > daily greatest * 1.05 | Inequality test: left expression must be strictly greater than right. |
| 8 | Enabled | daily market cap > 1000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 9 | Enabled | daily market cap < 10000 | Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 10 | Enabled | daily high = daily max( 90 ,  daily high ) | Equality test between left and right expressions. max(N, series) is the highest value of series over N bars. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily low < daily least * 0.95` — Inequality test: left expression must be strictly less than right.
- **#3** `daily market cap > 1000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#4** `daily market cap < 10000` — Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#5** `daily high = daily max( 90 ,  daily high )` — Equality test between left and right expressions. max(N, series) is the highest value of series over N bars.
- **#7** `daily high > daily greatest * 1.05` — Inequality test: left expression must be strictly greater than right.
- **#8** `daily market cap > 1000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#9** `daily market cap < 10000` — Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#10** `daily high = daily max( 90 ,  daily high )` — Equality test between left and right expressions. max(N, series) is the highest value of series over N bars.

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
- `high` — appears 5 time(s) in the expression tree
- `market cap` — appears 4 time(s) in the expression tree
- `open` — appears 2 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `least` — appears 1 time(s) in the expression tree
- `greatest` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 3 occurrence(s)
- `>` — 3 occurrence(s)
- `*` — 2 occurrence(s)
- `=` — 2 occurrence(s)

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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Moving average, Fundamental, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Breakout, Moving average, Fundamental, Multi-factor
- **Tags:** universe:cash, indicator:sma, timeframe:daily
- **Root universe:** cash
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

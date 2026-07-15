---
scan_id: 24392684
scan_name: Very Near to multi year high
source_url: https://chartink.com/screener/very-near-to-multi-year-hugh
market: Indian equities
horizon: Multi-horizon
classification: ["Breakout", "Fundamental", "Moving average", "Momentum", "Multi-factor"]
tags: ["universe:cash", "indicator:ema", "timeframe:weekly", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Breakout
---

# Very Near to multi year high

## Source

- Chartink URL: https://chartink.com/screener/very-near-to-multi-year-hugh
- Scan ID: `24392684`
- Slug: `very-near-to-multi-year-hugh`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2025-11-06T00:54:45.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24392684.json](../source-snapshots/24392684.json)
- Text snapshot: [source-snapshots/24392684.txt](../source-snapshots/24392684.txt)

## What this scan is for

This scan, titled "Very Near to multi year high", appears designed to screen Indian equities in the **cash** universe using **6 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Breakout, Fundamental, Moving average, Momentum**. Likely horizon label from name/timeframes: **Multi-horizon**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 0_quarters_ago, 0_weeks_ago, 1_quarters_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Very Near to multi year high
Scan id: 24392684
Slug: very-near-to-multi-year-hugh
Source URL: https://chartink.com/screener/very-near-to-multi-year-hugh
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-06T00:54:45.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily market cap > 3000
    group_path: root/group[cash|all]
3. [Enabled] 0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage
    group_path: root/group[cash|all]
4. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
5. [Enabled] daily close crossed above weekly max( 377 ,  weekly close ) * 0.98
    group_path: root/group[cash|any]
6. [Enabled] daily count( 89, 1 where daily close crossed above weekly max( 377 ,  weekly close ) * 0.98 ) >= 1
    group_path: root/group[cash|any]
7. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Enabled] daily ema( close ,  21 ) < daily ema( close ,  50 )
    group_path: root/group[cash|all]
9. [Enabled] daily count( 3, 1 where daily high > daily ema( close ,  21 ) ) crossed above 2
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( cash ( ( cash ( market cap > 3000 and quarterly foreign institutional investors percentage > 1 quarter ago foreign institutional investors percentage ) ) and( cash ( daily close > weekly max( 377 , weekly close ) * 0.98 and 1 day ago  close <= 1 week ago  max( 377 , weekly close )* 0.98 or daily count( 89, 1 where daily close > weekly max( 377 , weekly close ) * 0.98 and 1 day ago  close <= 1 week ago  max( 377 , weekly close )* 0.98 ) >= 1 ) ) and( cash ( daily ema( daily close , 21 ) < daily ema( daily close , 50 ) and daily count( 3, 1 where daily high > daily ema( daily close , 21 ) ) > 2 and 1 day ago  count( 3, 1 where daily high > 1 day ago  ema( daily close , 21 )) <= 2 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | daily market cap > 3000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 3 | Enabled | 0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage | Inequality test: left expression must be strictly greater than right. |
| 4 | Enabled | [GROUP segment=cash join=any combination=passes measurevalue=default] | Nested group over segment **cash** with join **any** (combination=passes). Group status=Enabled. |
| 5 | Enabled | daily close crossed above weekly max( 377 ,  weekly close ) * 0.98 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 6 | Enabled | daily count( 89, 1 where daily close crossed above weekly max( 377 ,  weekly close ) * 0.98 ) >= 1 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 7 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 8 | Enabled | daily ema( close ,  21 ) < daily ema( close ,  50 ) | Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field. |
| 9 | Enabled | daily count( 3, 1 where daily high > daily ema( close ,  21 ) ) crossed above 2 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). EMA is an exponentially weighted moving average of the chosen field. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily market cap > 3000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#3** `0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage` — Inequality test: left expression must be strictly greater than right.
- **#5** `daily close crossed above weekly max( 377 ,  weekly close ) * 0.98` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#6** `daily count( 89, 1 where daily close crossed above weekly max( 377 ,  weekly close ) * 0.98 ) >= 1` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#8** `daily ema( close ,  21 ) < daily ema( close ,  50 )` — Inequality test: left expression must be strictly less than right. EMA is an exponentially weighted moving average of the chosen field.
- **#9** `daily count( 3, 1 where daily high > daily ema( close ,  21 ) ) crossed above 2` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). EMA is an exponentially weighted moving average of the chosen field.

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
- `close` — appears 7 time(s) in the expression tree
- `ema` — appears 3 time(s) in the expression tree
- `foreign institutional investors percentage` — appears 2 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `count` — appears 2 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 3 occurrence(s)
- `crossed above` — 3 occurrence(s)
- `*` — 2 occurrence(s)
- `>=` — 1 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_quarters_ago`, `0_weeks_ago`, `1_quarters_ago`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Fundamental, Moving average, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Breakout, Fundamental, Moving average, Momentum, Multi-factor
- **Tags:** universe:cash, indicator:ema, timeframe:weekly, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 6420615
scan_name: New 52W Highs at least after 2 months downtrend
source_url: https://chartink.com/screener/new-52w-highs-at-least-after-2-months-downtrend
market: Indian equities
horizon: Swing
classification: ["Breakout", "Fundamental"]
tags: ["universe:nifty-200", "timeframe:weekly", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 10
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Breakout
---

# New 52W Highs at least after 2 months downtrend

## Source

- Chartink URL: https://chartink.com/screener/new-52w-highs-at-least-after-2-months-downtrend
- Scan ID: `6420615`
- Slug: `new-52w-highs-at-least-after-2-months-downtrend`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2021-10-05T17:12:55.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/6420615.json](../source-snapshots/6420615.json)
- Text snapshot: [source-snapshots/6420615.txt](../source-snapshots/6420615.txt)

## What this scan is for

This scan, titled "New 52W Highs at least after 2 months downtrend", appears designed to screen Indian equities in the **nifty 200** universe using **10 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Breakout, Fundamental**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 0_weeks_ago, 1_weeks_ago, 2_weeks_ago, 3_weeks_ago, 4_weeks_ago, 5_weeks_ago, 6_weeks_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: New 52W Highs at least after 2 months downtrend
Scan id: 6420615
Slug: new-52w-highs-at-least-after-2-months-downtrend
Source URL: https://chartink.com/screener/new-52w-highs-at-least-after-2-months-downtrend
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-10-05T17:12:55.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] weekly high > 1 week ago max( 52 ,  weekly high )
2. [Enabled] 1 week ago high <= 2 weeks ago max( 52 ,  weekly high )
3. [Enabled] 2 weeks ago high <= 3 weeks ago max( 52 ,  weekly high )
4. [Enabled] 3 weeks ago high <= 4 weeks ago max( 52 ,  weekly high )
5. [Enabled] 4 weeks ago high <= 5 weeks ago max( 52 ,  weekly high )
6. [Enabled] 5 weeks ago high <= 6 weeks ago max( 52 ,  weekly high )
7. [Enabled] 6 weeks ago high <= 7 weeks ago max( 52 ,  weekly high )
8. [Enabled] 7 weeks ago high <= 8 weeks ago max( 52 ,  weekly high )
9. [Enabled] 8 weeks ago high <= 9 weeks ago max( 52 ,  weekly high )
10. [Enabled] daily market cap >= 300

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( weekly high > 1 week ago max( 52 , weekly high ) and 1 week ago high <= 2 weeks ago max( 52 , weekly high ) and 2 weeks ago high <= 3 weeks ago max( 52 , weekly high ) and 3 weeks ago high <= 4 weeks ago max( 52 , weekly high ) and 4 weeks ago high <= 5 weeks ago max( 52 , weekly high ) and 5 weeks ago high <= 6 weeks ago max( 52 , weekly high ) and 6 weeks ago high <= 7 weeks ago max( 52 , weekly high ) and 7 weeks ago high <= 8 weeks ago max( 52 , weekly high ) and 8 weeks ago high <= 9 weeks ago max( 52 , weekly high ) and market cap >= 300 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | weekly high > 1 week ago max( 52 ,  weekly high ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 2 | Enabled | 1 week ago high <= 2 weeks ago max( 52 ,  weekly high ) | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 3 | Enabled | 2 weeks ago high <= 3 weeks ago max( 52 ,  weekly high ) | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 4 | Enabled | 3 weeks ago high <= 4 weeks ago max( 52 ,  weekly high ) | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 5 | Enabled | 4 weeks ago high <= 5 weeks ago max( 52 ,  weekly high ) | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 6 | Enabled | 5 weeks ago high <= 6 weeks ago max( 52 ,  weekly high ) | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 7 | Enabled | 6 weeks ago high <= 7 weeks ago max( 52 ,  weekly high ) | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 8 | Enabled | 7 weeks ago high <= 8 weeks ago max( 52 ,  weekly high ) | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 9 | Enabled | 8 weeks ago high <= 9 weeks ago max( 52 ,  weekly high ) | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 10 | Enabled | daily market cap >= 300 | Inequality test: left expression must be greater than or equal to right. Filters by market-capitalisation field from Chartink fundamentals. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **10** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `weekly high > 1 week ago max( 52 ,  weekly high )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#2** `1 week ago high <= 2 weeks ago max( 52 ,  weekly high )` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#3** `2 weeks ago high <= 3 weeks ago max( 52 ,  weekly high )` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#4** `3 weeks ago high <= 4 weeks ago max( 52 ,  weekly high )` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#5** `4 weeks ago high <= 5 weeks ago max( 52 ,  weekly high )` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#6** `5 weeks ago high <= 6 weeks ago max( 52 ,  weekly high )` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#7** `6 weeks ago high <= 7 weeks ago max( 52 ,  weekly high )` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#8** `7 weeks ago high <= 8 weeks ago max( 52 ,  weekly high )` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#9** `8 weeks ago high <= 9 weeks ago max( 52 ,  weekly high )` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#10** `daily market cap >= 300` — Inequality test: left expression must be greater than or equal to right. Filters by market-capitalisation field from Chartink fundamentals.

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
- `high` — appears 18 time(s) in the expression tree
- `max` — appears 9 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree

### Operators observed
- `<=` — 8 occurrence(s)
- `>` — 1 occurrence(s)
- `>=` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `1_weeks_ago`, `2_weeks_ago`, `3_weeks_ago`, `4_weeks_ago`, `5_weeks_ago`, `6_weeks_ago`, `7_weeks_ago`, `8_weeks_ago`, `9_weeks_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Breakout, Fundamental.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **10** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Breakout, Fundamental
- **Tags:** universe:nifty-200, timeframe:weekly, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

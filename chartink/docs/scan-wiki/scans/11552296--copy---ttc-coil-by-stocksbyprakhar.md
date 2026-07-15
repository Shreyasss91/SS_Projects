---
scan_id: 11552296
scan_name: "Copy - TTC COIL by @Stocksbyprakhar"
source_url: https://chartink.com/screener/copy-ttc-coil-by-atstocksbyprakhar-65
market: Indian equities
horizon: Swing
classification: ["Fundamental", "Moving average", "Volume/delivery", "Breakout", "Volatility", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "indicator:volume", "indicator:sma", "timeframe:daily", "timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 18
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Fundamental
---

# Copy - TTC COIL by @Stocksbyprakhar

## Source

- Chartink URL: https://chartink.com/screener/copy-ttc-coil-by-atstocksbyprakhar-65
- Scan ID: `11552296`
- Slug: `copy-ttc-coil-by-atstocksbyprakhar-65`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-04-23T02:26:46.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11552296.json](../source-snapshots/11552296.json)
- Text snapshot: [source-snapshots/11552296.txt](../source-snapshots/11552296.txt)

## What this scan is for

This is a **swing** screen over **cash** with **18** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Fundamental, Moving average, Volume/delivery, Breakout, Volatility, Multi-factor**.
The active tests, in captured order, are:
- daily high < 3 days ago high
- daily low > 3 days ago low
- 1 day ago high < 3 days ago high
- 1 day ago low > 3 days ago low
- 2 days ago high < 3 days ago high
- 2 days ago low > 3 days ago low
- daily close > daily sma( close ,  50 )
- ( daily close - daily sma( close ,  50 ) / daily sma( close ,  50 ) ) < 0.16
- daily sma( close,50 ) > daily sma( close,150 )
- daily close > daily sma( close,150 )
- daily close > daily sma( close,200 )
- daily sma( close,150 ) > daily sma( close,200 )
- daily sma( close,50 ) > daily sma( close,200 )
- daily close > weekly max( 52 ,  weekly high ) * 0.75
- daily volume > 5000
- daily market cap <= 40000
- daily max( 23 ,  daily high ) / daily min( 23 ,  daily low ) <= 1.20
- daily max( 5 ,  daily high ) / daily min( 5 ,  daily low ) <= 1.14

Author description (source metadata): https://twitter.com/StocksbyPrakhar/status/1649498467432284160

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - TTC COIL by @Stocksbyprakhar
Scan id: 11552296
Slug: copy-ttc-coil-by-atstocksbyprakhar-65
Source URL: https://chartink.com/screener/copy-ttc-coil-by-atstocksbyprakhar-65
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-23T02:26:46.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily high < 3 days ago high
2. [Enabled] daily low > 3 days ago low
3. [Enabled] 1 day ago high < 3 days ago high
4. [Enabled] 1 day ago low > 3 days ago low
5. [Enabled] 2 days ago high < 3 days ago high
6. [Enabled] 2 days ago low > 3 days ago low
7. [Enabled] daily close > daily sma( close ,  50 )
8. [Enabled] ( daily close - daily sma( close ,  50 ) / daily sma( close ,  50 ) ) < 0.16
9. [Enabled] daily sma( close,50 ) > daily sma( close,150 )
10. [Enabled] daily close > daily sma( close,150 )
11. [Enabled] daily close > daily sma( close,200 )
12. [Enabled] daily sma( close,150 ) > daily sma( close,200 )
13. [Enabled] daily sma( close,50 ) > daily sma( close,200 )
14. [Enabled] daily close > weekly max( 52 ,  weekly high ) * 0.75
15. [Enabled] daily volume > 5000
16. [Enabled] daily market cap <= 40000
17. [Enabled] daily max( 23 ,  daily high ) / daily min( 23 ,  daily low ) <= 1.20
18. [Enabled] daily max( 5 ,  daily high ) / daily min( 5 ,  daily low ) <= 1.14

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( latest high < 3 days ago high and latest low > 3 days ago low and 1 day ago high < 3 days ago high and 1 day ago low > 3 days ago low and 2 days ago high < 3 days ago high and 2 days ago low > 3 days ago low and latest close > latest sma( latest close , 50 ) and( latest close - latest sma( latest close , 50 ) / latest sma( latest close , 50 ) ) < 0.16 and latest sma( close,50 ) > latest sma( close,150 ) and latest close > latest sma( close,150 ) and latest close > latest sma( close,200 ) and latest sma( close,150 ) > latest sma( close,200 ) and latest sma( close,50 ) > latest sma( close,200 ) and latest close > weekly max( 52 , weekly high ) * 0.75 and latest volume > 5000 and market cap <= 40000 and latest max( 23 , latest high ) / latest min( 23 , latest low ) <= 1.20 and latest max( 5 , latest high ) / latest min( 5 , latest low ) <= 1.14 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily high < 3 days ago high | Inequality test: left expression must be strictly less than right. |
| 2 | 2 | Enabled | root | daily low > 3 days ago low | Inequality test: left expression must be strictly greater than right. |
| 3 | 3 | Enabled | root | 1 day ago high < 3 days ago high | Inequality test: left expression must be strictly less than right. |
| 4 | 4 | Enabled | root | 1 day ago low > 3 days ago low | Inequality test: left expression must be strictly greater than right. |
| 5 | 5 | Enabled | root | 2 days ago high < 3 days ago high | Inequality test: left expression must be strictly less than right. |
| 6 | 6 | Enabled | root | 2 days ago low > 3 days ago low | Inequality test: left expression must be strictly greater than right. |
| 7 | 7 | Enabled | root | daily close > daily sma( close ,  50 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 8 | 8 | Enabled | root | ( daily close - daily sma( close ,  50 ) / daily sma( close ,  50 ) ) < 0.16 | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 9 | 9 | Enabled | root | daily sma( close,50 ) > daily sma( close,150 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 10 | 10 | Enabled | root | daily close > daily sma( close,150 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 11 | 11 | Enabled | root | daily close > daily sma( close,200 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 12 | 12 | Enabled | root | daily sma( close,150 ) > daily sma( close,200 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 13 | 13 | Enabled | root | daily sma( close,50 ) > daily sma( close,200 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 14 | 14 | Enabled | root | daily close > weekly max( 52 ,  weekly high ) * 0.75 | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 15 | 15 | Enabled | root | daily volume > 5000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 16 | 16 | Enabled | root | daily market cap <= 40000 | Inequality test: left expression must be less than or equal to right. Filters by market-capitalisation field from Chartink fundamentals. |
| 17 | 17 | Enabled | root | daily max( 23 ,  daily high ) / daily min( 23 ,  daily low ) <= 1.20 | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 18 | 18 | Enabled | root | daily max( 5 ,  daily high ) / daily min( 5 ,  daily low ) <= 1.14 | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **18** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily high < 3 days ago high` — Inequality test: left expression must be strictly less than right.
- **#2** `daily low > 3 days ago low` — Inequality test: left expression must be strictly greater than right.
- **#3** `1 day ago high < 3 days ago high` — Inequality test: left expression must be strictly less than right.
- **#4** `1 day ago low > 3 days ago low` — Inequality test: left expression must be strictly greater than right.
- **#5** `2 days ago high < 3 days ago high` — Inequality test: left expression must be strictly less than right.
- **#6** `2 days ago low > 3 days ago low` — Inequality test: left expression must be strictly greater than right.
- **#7** `daily close > daily sma( close ,  50 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#8** `( daily close - daily sma( close ,  50 ) / daily sma( close ,  50 ) ) < 0.16` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#9** `daily sma( close,50 ) > daily sma( close,150 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#10** `daily close > daily sma( close,150 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#11** `daily close > daily sma( close,200 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#12** `daily sma( close,150 ) > daily sma( close,200 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#13** `daily sma( close,50 ) > daily sma( close,200 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#14** `daily close > weekly max( 52 ,  weekly high ) * 0.75` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#15** `daily volume > 5000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#16** `daily market cap <= 40000` — Inequality test: left expression must be less than or equal to right. Filters by market-capitalisation field from Chartink fundamentals.
- **#17** `daily max( 23 ,  daily high ) / daily min( 23 ,  daily low ) <= 1.20` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#18** `daily max( 5 ,  daily high ) / daily min( 5 ,  daily low ) <= 1.14` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

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
- `sma` — appears 11 time(s) in the expression tree
- `high` — appears 9 time(s) in the expression tree
- `low` — appears 8 time(s) in the expression tree
- `close` — appears 8 time(s) in the expression tree
- `max` — appears 3 time(s) in the expression tree
- `min` — appears 2 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 11 occurrence(s)
- `<` — 4 occurrence(s)
- `<=` — 3 occurrence(s)
- `/` — 2 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental, Moving average, Volume/delivery, Breakout, Volatility, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **18** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Fundamental, Moving average, Volume/delivery, Breakout, Volatility, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, indicator:volume, indicator:sma, timeframe:daily, timeframe:weekly
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

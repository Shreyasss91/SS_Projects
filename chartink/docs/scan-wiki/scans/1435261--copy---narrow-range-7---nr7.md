---
scan_id: 1435261
scan_name: Copy - Narrow Range 7 - NR7
source_url: https://chartink.com/screener/copy-narrow-range-7-nr7-717
market: Indian equities
horizon: Swing
classification: ["Moving average", "Volume/delivery"]
tags: ["universe:futures", "indicator:volume", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 9
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Moving average
---

# Copy - Narrow Range 7 - NR7

## Source

- Chartink URL: https://chartink.com/screener/copy-narrow-range-7-nr7-717
- Scan ID: `1435261`
- Slug: `copy-narrow-range-7-nr7-717`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2019-11-19T18:41:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1435261.json](../source-snapshots/1435261.json)
- Text snapshot: [source-snapshots/1435261.txt](../source-snapshots/1435261.txt)

## What this scan is for

This scan, titled "Copy - Narrow Range 7 - NR7", appears designed to screen Indian equities in the **futures** universe using **9 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Moving average, Volume/delivery**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 2_days_ago, 3_days_ago, 4_days_ago, 5_days_ago, 6_days_ago, 7_days_ago`.

Author description (source metadata): Market goes thru regular contraction (i.e. daily trading range getting shorter and shorter) and expansion (i.e. daily trading range getting bigger) cycle. Expanding range is followed by Contraction and vice-versa. So if we can identify the narrow range days, then it give us a step ahead of everybody to benefit from coming expansion.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Copy - Narrow Range 7 - NR7
Scan id: 1435261
Slug: copy-narrow-range-7-nr7-717
Source URL: https://chartink.com/screener/copy-narrow-range-7-nr7-717
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-19T18:41:56.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] 1 day ago high - 1 day ago low < 2 days ago high - 2 days ago low
2. [Enabled] 1 day ago high - 1 day ago low < 3 days ago high - 3 days ago low
3. [Enabled] 1 day ago high - 1 day ago low < 4 days ago high - 4 days ago low
4. [Enabled] 1 day ago high - 1 day ago low < 5 days ago high - 5 days ago low
5. [Enabled] 1 day ago high - 1 day ago low < 6 days ago high - 6 days ago low
6. [Enabled] 1 day ago high - 1 day ago low < 7 days ago high - 7 days ago low
7. [Enabled] daily sma( close,10 ) > daily sma( close,50 )
8. [Enabled] daily sma( close,50 ) > daily sma( close,200 )
9. [Enabled] daily volume > 50000

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( 1 day ago high - 1 day ago low < 2 days ago high - 2 days ago low and 1 day ago high - 1 day ago low < 3 days ago high - 3 days ago low and 1 day ago high - 1 day ago low < 4 days ago high - 4 days ago low and 1 day ago high - 1 day ago low < 5 days ago high - 5 days ago low and 1 day ago high - 1 day ago low < 6 days ago high - 6 days ago low and 1 day ago high - 1 day ago low < 7 days ago high - 7 days ago low and latest sma( close,10 ) > latest sma( close,50 ) and latest sma( close,50 ) > latest sma( close,200 ) and latest volume > 50000 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | 1 day ago high - 1 day ago low < 2 days ago high - 2 days ago low | Inequality test: left expression must be strictly less than right. |
| 2 | Enabled | 1 day ago high - 1 day ago low < 3 days ago high - 3 days ago low | Inequality test: left expression must be strictly less than right. |
| 3 | Enabled | 1 day ago high - 1 day ago low < 4 days ago high - 4 days ago low | Inequality test: left expression must be strictly less than right. |
| 4 | Enabled | 1 day ago high - 1 day ago low < 5 days ago high - 5 days ago low | Inequality test: left expression must be strictly less than right. |
| 5 | Enabled | 1 day ago high - 1 day ago low < 6 days ago high - 6 days ago low | Inequality test: left expression must be strictly less than right. |
| 6 | Enabled | 1 day ago high - 1 day ago low < 7 days ago high - 7 days ago low | Inequality test: left expression must be strictly less than right. |
| 7 | Enabled | daily sma( close,10 ) > daily sma( close,50 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 8 | Enabled | daily sma( close,50 ) > daily sma( close,200 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 9 | Enabled | daily volume > 50000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **9** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago high - 1 day ago low < 2 days ago high - 2 days ago low` — Inequality test: left expression must be strictly less than right.
- **#2** `1 day ago high - 1 day ago low < 3 days ago high - 3 days ago low` — Inequality test: left expression must be strictly less than right.
- **#3** `1 day ago high - 1 day ago low < 4 days ago high - 4 days ago low` — Inequality test: left expression must be strictly less than right.
- **#4** `1 day ago high - 1 day ago low < 5 days ago high - 5 days ago low` — Inequality test: left expression must be strictly less than right.
- **#5** `1 day ago high - 1 day ago low < 6 days ago high - 6 days ago low` — Inequality test: left expression must be strictly less than right.
- **#6** `1 day ago high - 1 day ago low < 7 days ago high - 7 days ago low` — Inequality test: left expression must be strictly less than right.
- **#7** `daily sma( close,10 ) > daily sma( close,50 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#8** `daily sma( close,50 ) > daily sma( close,200 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#9** `daily volume > 50000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.

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
- `high` — appears 12 time(s) in the expression tree
- `low` — appears 12 time(s) in the expression tree
- `sma` — appears 4 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `-` — 12 occurrence(s)
- `<` — 6 occurrence(s)
- `>` — 3 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **futures**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`, `4_days_ago`, `5_days_ago`, `6_days_ago`, `7_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **9** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Moving average, Volume/delivery
- **Tags:** universe:futures, indicator:volume, indicator:sma, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

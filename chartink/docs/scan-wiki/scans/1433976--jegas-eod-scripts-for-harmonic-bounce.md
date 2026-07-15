---
scan_id: 1433976
scan_name: "Jega's EOD Scripts for Harmonic Bounce"
source_url: https://chartink.com/screener/copy-jega-s-eod-scripts-for-harmonic-bounce-5
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volatility"]
tags: ["universe:futures", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 7
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Moving average
---

# Jega's EOD Scripts for Harmonic Bounce

## Source

- Chartink URL: https://chartink.com/screener/copy-jega-s-eod-scripts-for-harmonic-bounce-5
- Scan ID: `1433976`
- Slug: `copy-jega-s-eod-scripts-for-harmonic-bounce-5`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2019-11-19T12:41:00.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1433976.json](../source-snapshots/1433976.json)
- Text snapshot: [source-snapshots/1433976.txt](../source-snapshots/1433976.txt)

## What this scan is for

This scan, titled "Jega's EOD Scripts for Harmonic Bounce", appears designed to screen Indian equities in the **futures** universe using **7 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Moving average, Volatility**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 2_days_ago`.

Author description (source metadata): To make Intra Charts with PRZ for Short Entry by hidding inside day condition most of time

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Jega's EOD Scripts for Harmonic Bounce
Scan id: 1433976
Slug: copy-jega-s-eod-scripts-for-harmonic-bounce-5
Source URL: https://chartink.com/screener/copy-jega-s-eod-scripts-for-harmonic-bounce-5
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-19T12:41:00.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] daily williamsr( 14 ) < -80
2. [Enabled] daily lower bollinger band( 20,2 ) <= daily low
3. [Enabled] daily close < 1 day ago close
4. [Enabled] 1 day ago close < 2 days ago close
5. [Enabled] daily close < daily sma( close,20 )
6. [Enabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|all])
7. [Enabled] daily high < 1 day ago high
    group_path: root/group[futures|all]
8. [Enabled] daily low > 1 day ago low
    group_path: root/group[futures|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( latest williams %r( 14 ) < -80 and latest lower bollinger band( 20,2 ) <= latest low and latest close < 1 day ago close and 1 day ago close < 2 days ago close and latest close < latest sma( close,20 ) and( futures ( latest high < 1 day ago high and latest low > 1 day ago low ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | daily williamsr( 14 ) < -80 | Inequality test: left expression must be strictly less than right. |
| 2 | Enabled | daily lower bollinger band( 20,2 ) <= daily low | Inequality test: left expression must be less than or equal to right. Bollinger fields are typically a moving average ± standard-deviation bands. |
| 3 | Enabled | daily close < 1 day ago close | Inequality test: left expression must be strictly less than right. |
| 4 | Enabled | 1 day ago close < 2 days ago close | Inequality test: left expression must be strictly less than right. |
| 5 | Enabled | daily close < daily sma( close,20 ) | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. |
| 6 | Enabled | [GROUP segment=futures join=all combination=passes measurevalue=default] | Nested group over segment **futures** with join **all** (combination=passes). Group status=Enabled. |
| 7 | Enabled | daily high < 1 day ago high | Inequality test: left expression must be strictly less than right. |
| 8 | Enabled | daily low > 1 day ago low | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **7** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily williamsr( 14 ) < -80` — Inequality test: left expression must be strictly less than right.
- **#2** `daily lower bollinger band( 20,2 ) <= daily low` — Inequality test: left expression must be less than or equal to right. Bollinger fields are typically a moving average ± standard-deviation bands.
- **#3** `daily close < 1 day ago close` — Inequality test: left expression must be strictly less than right.
- **#4** `1 day ago close < 2 days ago close` — Inequality test: left expression must be strictly less than right.
- **#5** `daily close < daily sma( close,20 )` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars.
- **#7** `daily high < 1 day ago high` — Inequality test: left expression must be strictly less than right.
- **#8** `daily low > 1 day ago low` — Inequality test: left expression must be strictly greater than right.

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
- `close` — appears 5 time(s) in the expression tree
- `low` — appears 3 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree
- `williamsr` — appears 1 time(s) in the expression tree
- `lower bollinger band` — appears 1 time(s) in the expression tree
- `sma` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 5 occurrence(s)
- `<=` — 1 occurrence(s)
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
- Universe/segment: **futures**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volatility.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **7** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Moving average, Volatility
- **Tags:** universe:futures, indicator:sma, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

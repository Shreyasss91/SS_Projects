---
scan_id: 1430592
scan_name: Bollinger band Squeeze and NR -- DAILY TIMEFRAME
source_url: https://chartink.com/screener/copy-bollinger-band-squeeze-and-nr-1
market: Indian equities
horizon: Swing
classification: ["Volatility"]
tags: ["universe:nifty-50", "indicator:bollinger", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Volatility
---

# Bollinger band Squeeze and NR -- DAILY TIMEFRAME

## Source

- Chartink URL: https://chartink.com/screener/copy-bollinger-band-squeeze-and-nr-1
- Scan ID: `1430592`
- Slug: `copy-bollinger-band-squeeze-and-nr-1`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2019-11-18T11:20:58.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1430592.json](../source-snapshots/1430592.json)
- Text snapshot: [source-snapshots/1430592.txt](../source-snapshots/1430592.txt)

## What this scan is for

This scan, titled "Bollinger band Squeeze and NR -- DAILY TIMEFRAME", appears designed to screen Indian equities in the **nifty 500** universe using **4 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Volatility**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago`.

Author description (source metadata): Bollinger band Squeeze in Narrow Range

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Bollinger band Squeeze and NR -- DAILY TIMEFRAME
Scan id: 1430592
Slug: copy-bollinger-band-squeeze-and-nr-1
Source URL: https://chartink.com/screener/copy-bollinger-band-squeeze-and-nr-1
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-18T11:20:58.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] daily upper bollinger band( 20,2 ) - daily lower bollinger band( 20,2 ) <= daily avg true range( 14 ) * 2
2. [Enabled] daily close < 1500
3. [Enabled] daily close > 50
4. [Enabled] ( daily high - daily low ) < 1 day ago min( 6 ,  daily high - daily low )

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 500 ( latest upper bollinger band( 20,2 ) - latest lower bollinger band( 20,2 ) <= latest avg true range( 14 ) * 2 and latest close < 1500 and latest close > 50 and( latest high - latest low ) < 1 day ago min( 6 , latest high - latest low ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | daily upper bollinger band( 20,2 ) - daily lower bollinger band( 20,2 ) <= daily avg true range( 14 ) * 2 | Inequality test: left expression must be less than or equal to right. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction. |
| 2 | Enabled | daily close < 1500 | Inequality test: left expression must be strictly less than right. |
| 3 | Enabled | daily close > 50 | Inequality test: left expression must be strictly greater than right. |
| 4 | Enabled | ( daily high - daily low ) < 1 day ago min( 6 ,  daily high - daily low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily upper bollinger band( 20,2 ) - daily lower bollinger band( 20,2 ) <= daily avg true range( 14 ) * 2` — Inequality test: left expression must be less than or equal to right. Bollinger fields are typically a moving average ± standard-deviation bands. ATR measures smoothed true range (volatility), not direction.
- **#2** `daily close < 1500` — Inequality test: left expression must be strictly less than right.
- **#3** `daily close > 50` — Inequality test: left expression must be strictly greater than right.
- **#4** `( daily high - daily low ) < 1 day ago min( 6 ,  daily high - daily low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.

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
- `close` — appears 2 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree
- `low` — appears 2 time(s) in the expression tree
- `upper bollinger band` — appears 1 time(s) in the expression tree
- `lower bollinger band` — appears 1 time(s) in the expression tree
- `avg true range` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 2 occurrence(s)
- `-` — 1 occurrence(s)
- `<=` — 1 occurrence(s)
- `*` — 1 occurrence(s)
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
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volatility
- **Tags:** universe:nifty-50, indicator:bollinger, timeframe:daily
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 1432082
scan_name: MULTIPLE HULL MA BUNDLING
source_url: https://chartink.com/screener/copy-close-above-hull-moving-average-20-70
market: Indian equities
horizon: Unspecified
classification: ["Moving average"]
tags: ["universe:nifty-50"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 500
root_join: all
primary_classification: Moving average
---

# MULTIPLE HULL MA BUNDLING

## Source

- Chartink URL: https://chartink.com/screener/copy-close-above-hull-moving-average-20-70
- Scan ID: `1432082`
- Slug: `copy-close-above-hull-moving-average-20-70`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Unspecified
- Created at (Chartink): 2019-11-18T18:52:46.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1432082.json](../source-snapshots/1432082.json)
- Text snapshot: [source-snapshots/1432082.txt](../source-snapshots/1432082.txt)

## What this scan is for

This scan, titled "MULTIPLE HULL MA BUNDLING", appears designed to screen Indian equities in the **nifty 500** universe using **2 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Moving average**. Likely horizon label from name/timeframes: **Unspecified**.

Observed Chartink timeframe offsets in the tree: `1_days_ago`.

Author description (source metadata): Hull MA= WMA (2*WMA (n/2) − WMA (n)), sqrt (n))
na = 20
sqrt(20) = 4.4(rounding off to 4)

TIMEFRAME:DAILY
LATEST (HULLMA(200) - HULLMA(400)) < 0.5% OF LATEST CLOSE ==> HULLMA(200) AND HULL(400) ARE VERY CLOSE

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: MULTIPLE HULL MA BUNDLING
Scan id: 1432082
Slug: copy-close-above-hull-moving-average-20-70
Source URL: https://chartink.com/screener/copy-close-above-hull-moving-average-20-70
Root universe/segment: nifty 500
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-18T18:52:46.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] ( daily abs( 1 day ago wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - 1 day ago wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( 1 day ago close / 200 )
2. [Enabled] ( daily abs( 1 day ago wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - 1 day ago wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( 1 day ago close / 200 )

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 500 ( ( abs( 1 day ago wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - 1 day ago wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( 1 day ago close / 200 ) and( abs( 1 day ago wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - 1 day ago wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( 1 day ago close / 200 ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | ( daily abs( 1 day ago wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - 1 day ago wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( 1 day ago close / 200 ) | Inequality test: left expression must be less than or equal to right. |
| 2 | Enabled | ( daily abs( 1 day ago wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - 1 day ago wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( 1 day ago close / 200 ) | Inequality test: left expression must be less than or equal to right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `( daily abs( 1 day ago wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - 1 day ago wma( ( 2 * wma(close,200) - wma(close,400) ),20 ) ) ) <= ( 1 day ago close / 200 )` — Inequality test: left expression must be less than or equal to right.
- **#2** `( daily abs( 1 day ago wma( ( 2 * wma(close,100) - wma(close,200) ),14 ) - 1 day ago wma( ( 2 * wma(close,150) - wma(close,300) ),17 ) ) ) <= ( 1 day ago close / 200 )` — Inequality test: left expression must be less than or equal to right.

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
- `wma` — appears 4 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `abs` — appears 2 time(s) in the expression tree

### Operators observed
- `<=` — 2 occurrence(s)

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
- Timeframe tokens: `1_days_ago`

## How to use it

- **Horizon context:** treat as **Unspecified** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Unspecified
- **Methods:** Moving average
- **Tags:** universe:nifty-50
- **Root universe:** nifty 500
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

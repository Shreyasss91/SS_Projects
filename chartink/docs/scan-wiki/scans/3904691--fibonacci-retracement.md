---
scan_id: 3904691
scan_name: Fibonacci retracement
source_url: https://chartink.com/screener/fibonacci-retracement-89
market: Indian equities
horizon: Positional
classification: ["Price action"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "timeframe:daily", "timeframe:monthly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Price action
---

# Fibonacci retracement

## Source

- Chartink URL: https://chartink.com/screener/fibonacci-retracement-89
- Scan ID: `3904691`
- Slug: `fibonacci-retracement-89`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Positional
- Created at (Chartink): 2021-02-07T16:04:19.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/3904691.json](../source-snapshots/3904691.json)
- Text snapshot: [source-snapshots/3904691.txt](../source-snapshots/3904691.txt)

## What this scan is for

This is a **positional** screen over **futures** with **2** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Price action**.
The active tests, in captured order, are:
- ( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) > 1 day ago close
- ( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) < daily close

Author description (source metadata): Fibonacci Retracement Screener

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Fibonacci retracement
Scan id: 3904691
Slug: fibonacci-retracement-89
Source URL: https://chartink.com/screener/fibonacci-retracement-89
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-02-07T16:04:19.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] ( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) > 1 day ago close
2. [Enabled] ( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) < daily close

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( ( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) > 1 day ago close and( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) < latest close ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | ( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) > 1 day ago close | Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset. |
| 2 | 2 | Enabled | root | ( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) < daily close | Inequality test: left expression must be strictly less than right. References monthly bars / monthly offset. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) > 1 day ago close` — Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset.
- **#2** `( monthly low + ( ( monthly high - monthly low ) * 0.9 ) ) < daily close` — Inequality test: left expression must be strictly less than right. References monthly bars / monthly offset.

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
- `low` — appears 4 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 1 occurrence(s)
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
- Universe/segment: **futures**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Positional** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Positional
- **Methods:** Price action
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, timeframe:daily, timeframe:monthly
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

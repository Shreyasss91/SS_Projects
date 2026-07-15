---
scan_id: 13928636
scan_name: High Tight Flag
source_url: https://chartink.com/screener/high-tight-flag-23353
market: Indian equities
horizon: Positional
classification: ["Other"]
tags: ["bias:upward-condition", "universe:cash", "timeframe:daily", "timeframe:monthly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Other
---

# High Tight Flag

## Source

- Chartink URL: https://chartink.com/screener/high-tight-flag-23353
- Scan ID: `13928636`
- Slug: `high-tight-flag-23353`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Positional
- Created at (Chartink): 2023-11-24T04:32:04.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/13928636.json](../source-snapshots/13928636.json)
- Text snapshot: [source-snapshots/13928636.txt](../source-snapshots/13928636.txt)

## What this scan is for

This is a **positional** screen over **cash** with **2** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Other**.
The active tests, in captured order, are:
- monthly % change > 100
- monthly % change + 1 month ago % change > 100

Author description (source metadata): one o the criteria
https://traderlion.com/technical-analysis/the-high-tight-flag-pattern/
sakatas homma

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: High Tight Flag
Scan id: 13928636
Slug: high-tight-flag-23353
Source URL: https://chartink.com/screener/high-tight-flag-23353
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-11-24T04:32:04.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
2. [Enabled] monthly % change > 100
    group_path: root/group[cash|any]
3. [Enabled] monthly % change + 1 month ago % change > 100
    group_path: root/group[cash|any]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( monthly "close - 1 candle ago close / 1 candle ago close * 100" > 100 or monthly "close - 1 candle ago close / 1 candle ago close * 100" + 1 month ago "close - 1 candle ago close / 1 candle ago close * 100" > 100 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|any] | monthly % change > 100 | Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset. |
| 2 | 3 | Enabled | root/group[cash\|any] | monthly % change + 1 month ago % change > 100 | Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `monthly % change > 100` — Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset.
- **#3** `monthly % change + 1 month ago % change > 100` — Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset.

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
- `% change` — appears 3 time(s) in the expression tree

### Operators observed
- `>` — 2 occurrence(s)
- `+` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `1_months_ago`

## How to use it

- **Horizon context:** treat as **Positional** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Other.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Positional
- **Methods:** Other
- **Tags:** bias:upward-condition, universe:cash, timeframe:daily, timeframe:monthly
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

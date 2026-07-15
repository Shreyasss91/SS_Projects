---
scan_id: 18857175
scan_name: cross prev month low and face buying and close above that low
source_url: https://chartink.com/screener/cross-prev-month-low-and-face-buying-and-close-above-that-low
market: Indian equities
horizon: Positional
classification: ["Price action"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-200", "timeframe:daily", "timeframe:monthly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Price action
---

# cross prev month low and face buying and close above that low

## Source

- Chartink URL: https://chartink.com/screener/cross-prev-month-low-and-face-buying-and-close-above-that-low
- Scan ID: `18857175`
- Slug: `cross-prev-month-low-and-face-buying-and-close-above-that-low`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Positional
- Created at (Chartink): 2024-10-05T05:43:22.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/18857175.json](../source-snapshots/18857175.json)
- Text snapshot: [source-snapshots/18857175.txt](../source-snapshots/18857175.txt)

## What this scan is for

This is a **positional** screen over **nifty 200** with **3** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Price action**.
The active tests, in captured order, are:
- 2 days ago low < 1 month ago low
- 1 day ago high > 1 month ago low
- daily close > 1 month ago low

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: cross prev month low and face buying and close above that low
Scan id: 18857175
Slug: cross-prev-month-low-and-face-buying-and-close-above-that-low
Source URL: https://chartink.com/screener/cross-prev-month-low-and-face-buying-and-close-above-that-low
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2024-10-05T05:43:22.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 2 days ago low < 1 month ago low
    group_path: root/group[cash|all]
3. [Enabled] 1 day ago high > 1 month ago low
    group_path: root/group[cash|all]
4. [Enabled] daily close > 1 month ago low
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( 2 days ago low < 1 month ago low and 1 day ago high > 1 month ago low and latest close > 1 month ago low ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 2 days ago low < 1 month ago low | Inequality test: left expression must be strictly less than right. References monthly bars / monthly offset. |
| 2 | 3 | Enabled | root/group[cash\|all] | 1 day ago high > 1 month ago low | Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily close > 1 month ago low | Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `2 days ago low < 1 month ago low` — Inequality test: left expression must be strictly less than right. References monthly bars / monthly offset.
- **#3** `1 day ago high > 1 month ago low` — Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset.
- **#4** `daily close > 1 month ago low` — Inequality test: left expression must be strictly greater than right. References monthly bars / monthly offset.

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
- `high` — appears 1 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 2 occurrence(s)
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
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `1_months_ago`, `2_days_ago`

## How to use it

- **Horizon context:** treat as **Positional** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Positional
- **Methods:** Price action
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-200, timeframe:daily, timeframe:monthly
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 24508146
scan_name: Virgin Pivot on Upside
source_url: https://chartink.com/screener/virgin-pivot-on-upside
market: Indian equities
horizon: Swing
classification: ["Support/resistance", "Momentum"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-200", "indicator:pivot", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 9
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: any
primary_classification: Support/resistance
---

# Virgin Pivot on Upside

## Source

- Chartink URL: https://chartink.com/screener/virgin-pivot-on-upside
- Scan ID: `24508146`
- Slug: `virgin-pivot-on-upside`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2025-11-17T04:47:07.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24508146.json](../source-snapshots/24508146.json)
- Text snapshot: [source-snapshots/24508146.txt](../source-snapshots/24508146.txt)

## What this scan is for

This is a **swing** screen over **nifty 200** with **9** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Support/resistance, Momentum**.
The active tests, in captured order, are:
- 1 day ago high < 1 day ago pivot point
- daily high crossed above 1 day ago pivot point
- 2 days ago high < 2 days ago pivot point
- 1 day ago high < 2 days ago pivot point
- daily high crossed above 2 days ago pivot point
- 3 days ago high < 3 days ago pivot point
- 2 days ago high < 3 days ago pivot point
- 1 day ago high < 3 days ago pivot point
- daily high crossed above 3 days ago pivot point

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Virgin Pivot on Upside
Scan id: 24508146
Slug: virgin-pivot-on-upside
Source URL: https://chartink.com/screener/virgin-pivot-on-upside
Root universe/segment: nifty 200
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-17T04:47:07.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago high < 1 day ago pivot point
    group_path: root/group[cash|all]
3. [Enabled] daily high crossed above 1 day ago pivot point
    group_path: root/group[cash|all]
4. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] 2 days ago high < 2 days ago pivot point
    group_path: root/group[cash|all]
6. [Enabled] 1 day ago high < 2 days ago pivot point
    group_path: root/group[cash|all]
7. [Enabled] daily high crossed above 2 days ago pivot point
    group_path: root/group[cash|all]
8. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
9. [Enabled] 3 days ago high < 3 days ago pivot point
    group_path: root/group[cash|all]
10. [Enabled] 2 days ago high < 3 days ago pivot point
    group_path: root/group[cash|all]
11. [Enabled] 1 day ago high < 3 days ago pivot point
    group_path: root/group[cash|all]
12. [Enabled] daily high crossed above 3 days ago pivot point
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( 3 days ago high < 3 days ago "(1 candle ago high + 1 candle ago low + 1 candle ago close / 3)" and 2 days ago high < 3 days ago "(1 candle ago high + 1 candle ago low + 1 candle ago close / 3)" and 1 day ago high < 3 days ago "(1 candle ago high + 1 candle ago low + 1 candle ago close / 3)" and daily high > 3 days ago "(1 candle ago high + 1 candle ago low + 1 candle ago close / 3)" and 1 day ago  high <= 3 days ago "(1 candle ago high + 1 candle ago low + 1 candle ago close / 3)" ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago high < 1 day ago pivot point | Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily high crossed above 1 day ago pivot point | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 3 | 5 | Enabled | root/group[cash\|all] | 2 days ago high < 2 days ago pivot point | Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 4 | 6 | Enabled | root/group[cash\|all] | 1 day ago high < 2 days ago pivot point | Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 5 | 7 | Enabled | root/group[cash\|all] | daily high crossed above 2 days ago pivot point | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 6 | 9 | Enabled | root/group[cash\|all] | 3 days ago high < 3 days ago pivot point | Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 7 | 10 | Enabled | root/group[cash\|all] | 2 days ago high < 3 days ago pivot point | Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 8 | 11 | Enabled | root/group[cash\|all] | 1 day ago high < 3 days ago pivot point | Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |
| 9 | 12 | Enabled | root/group[cash\|all] | daily high crossed above 3 days ago pivot point | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **9** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago high < 1 day ago pivot point` — Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#3** `daily high crossed above 1 day ago pivot point` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#5** `2 days ago high < 2 days ago pivot point` — Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#6** `1 day ago high < 2 days ago pivot point` — Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#7** `daily high crossed above 2 days ago pivot point` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#9** `3 days ago high < 3 days ago pivot point` — Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#10** `2 days ago high < 3 days ago pivot point` — Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#11** `1 day ago high < 3 days ago pivot point` — Inequality test: left expression must be strictly less than right. Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.
- **#12** `daily high crossed above 3 days ago pivot point` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `high` — appears 9 time(s) in the expression tree
- `pivot point` — appears 9 time(s) in the expression tree

### Operators observed
- `<` — 6 occurrence(s)
- `crossed above` — 3 occurrence(s)

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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Support/resistance, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **9** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Support/resistance, Momentum
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-200, indicator:pivot, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

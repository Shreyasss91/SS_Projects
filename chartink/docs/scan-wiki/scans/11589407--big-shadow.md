---
scan_id: 11589407
scan_name: big shadow
source_url: https://chartink.com/screener/big-wick-15
market: Indian equities
horizon: Swing
classification: ["Volatility"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:futures", "indicator:atr", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: any
primary_classification: Volatility
---

# big shadow

## Source

- Chartink URL: https://chartink.com/screener/big-wick-15
- Scan ID: `11589407`
- Slug: `big-wick-15`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-04-27T05:41:02.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11589407.json](../source-snapshots/11589407.json)
- Text snapshot: [source-snapshots/11589407.txt](../source-snapshots/11589407.txt)

## What this scan is for

This is a **swing** screen over **futures** with **2** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Volatility**.
The active tests, in captured order, are:
- daily high - daily greatest > daily avg true range( 14 )
- daily low - daily least < daily avg true range( 14 ) * -1

Author description (source metadata): big upper shadow means there are buyers who want to see price go up, within couple of days price may retest the wicks high(may be after a pullback) (can take longs at previous swing low or imp pivots) (T+1 candle shouldn't close below today's low otherwise it means bears are too stong and price maynot bounce)
similarly for big lower shadow

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: big shadow
Scan id: 11589407
Slug: big-wick-15
Source URL: https://chartink.com/screener/big-wick-15
Root universe/segment: futures
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-04-27T05:41:02.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily high - daily greatest > daily avg true range( 14 )
2. [Enabled] daily low - daily least < daily avg true range( 14 ) * -1

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( latest high - greatest(  latest open, latest close  ) > latest avg true range( 14 ) or latest low - least(  latest open, latest close  ) < latest avg true range( 14 ) * -1 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily high - daily greatest > daily avg true range( 14 ) | Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction. |
| 2 | 2 | Enabled | root | daily low - daily least < daily avg true range( 14 ) * -1 | Inequality test: left expression must be strictly less than right. ATR measures smoothed true range (volatility), not direction. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily high - daily greatest > daily avg true range( 14 )` — Inequality test: left expression must be strictly greater than right. ATR measures smoothed true range (volatility), not direction.
- **#2** `daily low - daily least < daily avg true range( 14 ) * -1` — Inequality test: left expression must be strictly less than right. ATR measures smoothed true range (volatility), not direction.

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
- `avg true range` — appears 2 time(s) in the expression tree
- `open` — appears 2 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `greatest` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `least` — appears 1 time(s) in the expression tree

### Operators observed
- `-` — 2 occurrence(s)
- `>` — 1 occurrence(s)
- `<` — 1 occurrence(s)
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
- Universe/segment: **futures**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volatility
- **Tags:** bias:upward-condition, bias:downward-condition, universe:futures, indicator:atr, timeframe:daily
- **Root universe:** futures
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

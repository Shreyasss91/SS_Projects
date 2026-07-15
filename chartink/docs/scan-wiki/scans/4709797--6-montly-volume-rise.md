---
scan_id: 4709797
scan_name: "6 Montly volume rise"
source_url: https://chartink.com/screener/6-montly-volume-rise
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery"]
tags: ["universe:futures","indicator:volume","timeframe:daily","timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 3
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# 6 Montly volume rise

## Source

- Chartink URL: https://chartink.com/screener/6-montly-volume-rise
- Scan ID: `4709797`
- Slug: `6-montly-volume-rise`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2021-05-28T09:19:29.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4709797.json](../source-snapshots/4709797.json)
- Text snapshot: [source-snapshots/4709797.txt](../source-snapshots/4709797.txt)

## What this scan is for

This is a **swing** screen over **futures** with **3** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
- daily count streak( 5, 1 where daily volume > 1 week ago volume * 1 ) >= 3

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: 6 Montly volume rise
Scan id: 4709797
Slug: 6-montly-volume-rise
Source URL: https://chartink.com/screener/6-montly-volume-rise
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-05-28T09:19:29.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close * 1 day ago volume > 100000000
2. [Enabled] daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
3. [Disabled] monthly sum( close ,  6 ) > 6 months ago sum( close ,  6 ) * 50
4. [Disabled] monthly sum( close ,  6 ) > 6 months ago sum( close ,  6 ) * 30
5. [Disabled] monthly sma( close ,  4 ) > 4 months ago sma( close ,  8 ) * 5
6. [Enabled] daily count streak( 5, 1 where daily volume > 1 week ago volume * 1 ) >= 3

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( 1 day ago close * 1 day ago volume > 100000000 and latest count( 200, 1 where( latest high / latest low ) = 1 ) < 1 and latest countstreak( 5, 1 where latest volume > 1 week ago volume * 1 ) >= 3 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 2 | Enabled | root | daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1 | Inequality test: left expression must be strictly less than right. |
| 3 | 3 | Disabled | root | monthly sum( close ,  6 ) > 6 months ago sum( close ,  6 ) * 50 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset. |
| 4 | 4 | Disabled | root | monthly sum( close ,  6 ) > 6 months ago sum( close ,  6 ) * 30 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset. |
| 5 | 5 | Disabled | root | monthly sma( close ,  4 ) > 4 months ago sma( close ,  8 ) * 5 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. References monthly bars / monthly offset. |
| 6 | 6 | Enabled | root | daily count streak( 5, 1 where daily volume > 1 week ago volume * 1 ) >= 3 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. References weekly bars / weekly offset. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#2** `daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1` — Inequality test: left expression must be strictly less than right.
- **#6** `daily count streak( 5, 1 where daily volume > 1 week ago volume * 1 ) >= 3` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. References weekly bars / weekly offset.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **3** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `monthly sum( close ,  6 ) > 6 months ago sum( close ,  6 ) * 50`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `monthly sum( close ,  6 ) > 6 months ago sum( close ,  6 ) * 30`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `monthly sma( close ,  4 ) > 4 months ago sma( close ,  8 ) * 5`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `volume` — appears 9 time(s) in the expression tree
- `sum` — appears 4 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `count streak` — appears 1 time(s) in the expression tree

### Operators observed
- `*` — 5 occurrence(s)
- `>` — 5 occurrence(s)
- `<` — 1 occurrence(s)
- `=` — 1 occurrence(s)
- `>=` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `0_weeks_ago`, `1_days_ago`, `1_weeks_ago`, `4_months_ago`, `6_months_ago`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Moving average.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **3** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery
- **Tags:** universe:futures, indicator:volume, timeframe:daily, timeframe:weekly
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

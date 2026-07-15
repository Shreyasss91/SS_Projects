---
scan_id: 4664681
scan_name: clvol retest
source_url: https://chartink.com/screener/clvol-retest
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery","Breakout","Momentum"]
tags: ["universe:cash","indicator:volume","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 4
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# clvol retest

## Source

- Chartink URL: https://chartink.com/screener/clvol-retest
- Scan ID: `4664681`
- Slug: `clvol-retest`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2021-05-24T16:07:33.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4664681.json](../source-snapshots/4664681.json)
- Text snapshot: [source-snapshots/4664681.txt](../source-snapshots/4664681.txt)

## What this scan is for

This is a **swing** screen over **cash** with **3** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Breakout, Momentum**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- ( daily max( 20 ,  daily high ) / daily min( 20 ,  daily low ) ) crossed above 1.5
- daily low < 1 day ago min( 20 ,  daily low )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: clvol retest
Scan id: 4664681
Slug: clvol-retest
Source URL: https://chartink.com/screener/clvol-retest
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-05-24T16:07:33.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Disabled] daily Cl*Vol crossed above 1 day ago max( 500 ,  daily Cl*Vol )
    group_path: root/group[cash|all]
4. [Disabled] 1 day ago max( 499 ,  daily Cl*Vol ) < 500 days ago max( 500 ,  daily Cl*Vol )
    group_path: root/group[cash|all]
5. [Disabled] daily Cl*Vol crossed above daily ema( close ,  200 )
    group_path: root/group[cash|all]
6. [Disabled] ( daily max( 30 ,  daily high ) / daily min( 30 ,  daily low ) ) < 1.08
    group_path: root/group[cash|all]
7. [Enabled] ( daily max( 20 ,  daily high ) / daily min( 20 ,  daily low ) ) crossed above 1.5
    group_path: root/group[cash|all]
8. [Enabled] daily low < 1 day ago min( 20 ,  daily low )
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and( latest max( 20 , latest high ) / latest min( 20 , latest low ) ) > 1.5 and( 1 day ago  max( 20 , latest high )/ 1 day ago  min( 20 , latest low )) <= 1.5 and latest low < 1 day ago min( 20 , latest low ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 3 | Disabled | root/group[cash\|all] | daily Cl*Vol crossed above 1 day ago max( 500 ,  daily Cl*Vol ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 3 | 4 | Disabled | root/group[cash\|all] | 1 day ago max( 499 ,  daily Cl*Vol ) < 500 days ago max( 500 ,  daily Cl*Vol ) | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 4 | 5 | Disabled | root/group[cash\|all] | daily Cl*Vol crossed above daily ema( close ,  200 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field. |
| 5 | 6 | Disabled | root/group[cash\|all] | ( daily max( 30 ,  daily high ) / daily min( 30 ,  daily low ) ) < 1.08 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 6 | 7 | Enabled | root/group[cash\|all] | ( daily max( 20 ,  daily high ) / daily min( 20 ,  daily low ) ) crossed above 1.5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 7 | 8 | Enabled | root/group[cash\|all] | daily low < 1 day ago min( 20 ,  daily low ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#7** `( daily max( 20 ,  daily high ) / daily min( 20 ,  daily low ) ) crossed above 1.5` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#8** `daily low < 1 day ago min( 20 ,  daily low )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **4** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily Cl*Vol crossed above 1 day ago max( 500 ,  daily Cl*Vol )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `1 day ago max( 499 ,  daily Cl*Vol ) < 500 days ago max( 500 ,  daily Cl*Vol )`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily Cl*Vol crossed above daily ema( close ,  200 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. EMA is an exponentially weighted moving average of the chosen field.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `( daily max( 30 ,  daily high ) / daily min( 30 ,  daily low ) ) < 1.08`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `custom_indicator_19628` — appears 6 time(s) in the expression tree
- `max` — appears 5 time(s) in the expression tree
- `low` — appears 4 time(s) in the expression tree
- `min` — appears 3 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree
- `ema` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 3 occurrence(s)
- `<` — 3 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `20_days_ago`, `21_days_ago`, `500_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Mean reversion, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Stretch conditions can highlight exhaustion zones inside ranges when broader trend is not strongly opposed.
- Retains **4** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Mean-reversion style thresholds can **fight strong trends** and produce repeated losers in momentum markets.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery, Breakout, Momentum
- **Tags:** universe:cash, indicator:volume, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

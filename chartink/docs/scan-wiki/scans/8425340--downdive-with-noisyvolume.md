---
scan_id: 8425340
scan_name: downdive with noisyvolume
source_url: https://chartink.com/screener/downdive-with-noisyvolume
market: Indian equities
horizon: "Intraday"
classification: ["Fundamental","Volume/delivery"]
tags: ["universe:nifty-200","indicator:volume","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Fundamental
---

# downdive with noisyvolume

## Source

- Chartink URL: https://chartink.com/screener/downdive-with-noisyvolume
- Scan ID: `8425340`
- Slug: `downdive-with-noisyvolume`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2022-04-25T11:46:24.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8425340.json](../source-snapshots/8425340.json)
- Text snapshot: [source-snapshots/8425340.txt](../source-snapshots/8425340.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **8** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Fundamental, Volume/delivery**.

The active tests, in captured order:
- daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
- daily market cap > 2000
- daily market cap < 4000
- daily % change < 1
- [0] 30 minute close < [-1] 30 minute close
- [0] 30 minute volume < [0] 30 minute min( 21 ,  ( [0] 30 minute close - [-1] 30 minute close ) / [0] 30 minute abs( [0] 30 minute close - [-1] 30 minute close ) * [0] 30 minute volume ) * -0.9
- daily buyer initiated trades ratio > 2
- daily buyer initiated trades quantity ratio > 2

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: downdive with noisyvolume
Scan id: 8425340
Slug: downdive-with-noisyvolume
Source URL: https://chartink.com/screener/downdive-with-noisyvolume
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-04-25T11:46:24.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1
    group_path: root/group[cash|all]
3. [Enabled] daily market cap > 2000
    group_path: root/group[cash|all]
4. [Enabled] daily market cap < 4000
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] daily % change < 1
    group_path: root/group[cash|all]
7. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Enabled] [0] 30 minute close < [-1] 30 minute close
    group_path: root/group[cash|all]
9. [Disabled] [0] 30 minute count( 21, 1 where [0] 30 minute close < [-1] 30 minute close ) >= 10
    group_path: root/group[cash|all]
10. [Enabled] [0] 30 minute volume < [0] 30 minute min( 21 ,  ( [0] 30 minute close - [-1] 30 minute close ) / [0] 30 minute abs( [0] 30 minute close - [-1] 30 minute close ) * [0] 30 minute volume ) * -0.9
    group_path: root/group[cash|all]
11. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
12. [Disabled] [0] 30 minute close < [-6] 30 minute close * 0.97
    group_path: root/group[cash|all]
13. [Enabled] daily buyer initiated trades ratio > 2
    group_path: root/group[cash|all]
14. [Enabled] daily buyer initiated trades quantity ratio > 2
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( latest "buyer initiated trades / seller initiated trades" > 2 and latest "buyer initiated trades quantity / seller initiated trades quantity" > 2 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1 | Inequality test: left expression must be strictly less than right. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily market cap > 2000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily market cap < 4000 | Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 4 | 6 | Enabled | root/group[cash\|all] | daily % change < 1 | Inequality test: left expression must be strictly less than right. |
| 5 | 8 | Enabled | root/group[cash\|all] | [0] 30 minute close < [-1] 30 minute close | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 9 | Disabled | root/group[cash\|all] | [0] 30 minute count( 21, 1 where [0] 30 minute close < [-1] 30 minute close ) >= 10 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 10 | Enabled | root/group[cash\|all] | [0] 30 minute volume < [0] 30 minute min( 21 ,  ( [0] 30 minute close - [-1] 30 minute close ) / [0] 30 minute abs( [0] 30 minute close - [-1] 30 minute close ) * [0] 30 minute volume ) * -0.9 | Inequality test: left expression must be strictly less than right. Volume condition gates participation/liquidity. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 12 | Disabled | root/group[cash\|all] | [0] 30 minute close < [-6] 30 minute close * 0.97 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 13 | Enabled | root/group[cash\|all] | daily buyer initiated trades ratio > 2 | Inequality test: left expression must be strictly greater than right. |
| 10 | 14 | Enabled | root/group[cash\|all] | daily buyer initiated trades quantity ratio > 2 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily count( 200, 1 where ( daily high / daily low ) = 1 ) < 1` — Inequality test: left expression must be strictly less than right.
- **#3** `daily market cap > 2000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#4** `daily market cap < 4000` — Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#6** `daily % change < 1` — Inequality test: left expression must be strictly less than right.
- **#8** `[0] 30 minute close < [-1] 30 minute close` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[0] 30 minute volume < [0] 30 minute min( 21 ,  ( [0] 30 minute close - [-1] 30 minute close ) / [0] 30 minute abs( [0] 30 minute close - [-1] 30 minute close ) * [0] 30 minute volume ) * -0.9` — Inequality test: left expression must be strictly less than right. Volume condition gates participation/liquidity. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#13** `daily buyer initiated trades ratio > 2` — Inequality test: left expression must be strictly greater than right.
- **#14** `daily buyer initiated trades quantity ratio > 2` — Inequality test: left expression must be strictly greater than right.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #9
- **Condition (verbatim):** `[0] 30 minute count( 21, 1 where [0] 30 minute close < [-1] 30 minute close ) >= 10`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `[0] 30 minute close < [-6] 30 minute close * 0.97`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 10 time(s) in the expression tree
- `count` — appears 2 time(s) in the expression tree
- `market cap` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `% change` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree
- `abs` — appears 1 time(s) in the expression tree
- `buyer initiated trades ratio` — appears 1 time(s) in the expression tree
- `buyer initiated trades quantity ratio` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 7 occurrence(s)
- `>` — 3 occurrence(s)
- `*` — 2 occurrence(s)
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
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `30_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Fundamental.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Fundamental, Volume/delivery
- **Tags:** universe:nifty-200, indicator:volume, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

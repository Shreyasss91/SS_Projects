---
scan_id: 24264248
scan_name: slow and fast vwap averages
source_url: https://chartink.com/screener/running-vwap
market: Indian equities
horizon: "Intraday"
classification: ["Fundamental","Moving average","Volume/delivery","Momentum"]
tags: ["universe:cash","indicator:sma","indicator:vwap","timeframe:daily","timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 7
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Fundamental
---

# slow and fast vwap averages

## Source

- Chartink URL: https://chartink.com/screener/running-vwap
- Scan ID: `24264248`
- Slug: `running-vwap`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2025-10-25T12:44:25.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24264248.json](../source-snapshots/24264248.json)
- Text snapshot: [source-snapshots/24264248.txt](../source-snapshots/24264248.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **7** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Fundamental, Moving average, Volume/delivery, Momentum**.

The active tests, in captured order:
- daily market cap > 4000
- [0] 30 minute close crossed below [0] 30 minute sma( close ,  233 )
- [0] 30 minute sma( close ,  144 ) > [0] 30 minute sma( close ,  233 ) * 1.015
- [0] 30 minute sma( close ,  144 ) crossed above [0] 30 minute sma( close ,  233 )
- [0] 30 minute close > [0] 30 minute sma( close ,  233 )
- [0] 30 minute close crossed above [0] 30 minute sma( close ,  233 )
- [0] 30 minute sma( close ,  144 ) < [0] 30 minute sma( close ,  233 ) * 0.985

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: slow and fast vwap averages
Scan id: 24264248
Slug: running-vwap
Source URL: https://chartink.com/screener/running-vwap
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-10-25T12:44:25.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily market cap > 4000
2. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Enabled] [0] 30 minute close crossed below [0] 30 minute sma( close ,  233 )
    group_path: root/group[cash|all]
4. [Enabled] [0] 30 minute sma( close ,  144 ) > [0] 30 minute sma( close ,  233 ) * 1.015
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] [0] 30 minute sma( close ,  144 ) crossed above [0] 30 minute sma( close ,  233 )
    group_path: root/group[cash|all]
7. [Enabled] [0] 30 minute close > [0] 30 minute sma( close ,  233 )
    group_path: root/group[cash|all]
8. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
9. [Enabled] [0] 30 minute close crossed above [0] 30 minute sma( close ,  233 )
    group_path: root/group[cash|all]
10. [Enabled] [0] 30 minute sma( close ,  144 ) < [0] 30 minute sma( close ,  233 ) * 0.985
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( market cap > 4000 and( cash ( [0] 30 minute close > [0] 30 minute sma( [0] 30 minute vwap , 233 ) and [ -1 ] 30 minute close <= [ -1 ] 30 minute sma( [0] 30 minute vwap , 233 ) and [0] 30 minute sma( [0] 30 minute vwap , 144 ) < [0] 30 minute sma( [0] 30 minute vwap , 233 ) * 0.985 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily market cap > 4000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 2 | 3 | Enabled | root/group[cash\|all] | [0] 30 minute close crossed below [0] 30 minute sma( close ,  233 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 4 | Enabled | root/group[cash\|all] | [0] 30 minute sma( close ,  144 ) > [0] 30 minute sma( close ,  233 ) * 1.015 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 6 | Enabled | root/group[cash\|all] | [0] 30 minute sma( close ,  144 ) crossed above [0] 30 minute sma( close ,  233 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 7 | Enabled | root/group[cash\|all] | [0] 30 minute close > [0] 30 minute sma( close ,  233 ) | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 9 | Enabled | root/group[cash\|all] | [0] 30 minute close crossed above [0] 30 minute sma( close ,  233 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 10 | Enabled | root/group[cash\|all] | [0] 30 minute sma( close ,  144 ) < [0] 30 minute sma( close ,  233 ) * 0.985 | Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **7** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily market cap > 4000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#3** `[0] 30 minute close crossed below [0] 30 minute sma( close ,  233 )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `[0] 30 minute sma( close ,  144 ) > [0] 30 minute sma( close ,  233 ) * 1.015` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[0] 30 minute sma( close ,  144 ) crossed above [0] 30 minute sma( close ,  233 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[0] 30 minute close > [0] 30 minute sma( close ,  233 )` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[0] 30 minute close crossed above [0] 30 minute sma( close ,  233 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `[0] 30 minute sma( close ,  144 ) < [0] 30 minute sma( close ,  233 ) * 0.985` — Inequality test: left expression must be strictly less than right. SMA is the arithmetic mean of the chosen field over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `sma` — appears 9 time(s) in the expression tree
- `vwap` — appears 9 time(s) in the expression tree
- `close` — appears 3 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 3 occurrence(s)
- `*` — 2 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `crossed below` — 1 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `30_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Fundamental, Moving average, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **7** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Fundamental, Moving average, Volume/delivery, Momentum
- **Tags:** universe:cash, indicator:sma, indicator:vwap, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

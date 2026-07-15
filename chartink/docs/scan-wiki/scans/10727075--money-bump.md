---
scan_id: 10727075
scan_name: money bump
source_url: https://chartink.com/screener/money-bump
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volatility", "Volume/delivery", "Trend following", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "indicator:volume", "indicator:sma", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 4
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Moving average
---

# money bump

## Source

- Chartink URL: https://chartink.com/screener/money-bump
- Scan ID: `10727075`
- Slug: `money-bump`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-01-05T10:34:54.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/10727075.json](../source-snapshots/10727075.json)
- Text snapshot: [source-snapshots/10727075.txt](../source-snapshots/10727075.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **8** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average, Volatility, Volume/delivery, Trend following, Momentum, Multi-factor**.
The active tests, in captured order, are:
- [0] 30 minute count( 800, 1 where [0] 30 minute sum( close ,  120 ) < 200 ) > 600
- [0] 30 minute sum( close ,  120 ) crossed above 200
- 1 day ago close * 1 day ago volume > 100000000
- [0] 30 minute count( 800, 1 where [0] 30 minute sum( close ,  120 ) < 60 ) > 600
- [0] 30 minute sum( close ,  120 ) crossed above 85
- 1 day ago close * 1 day ago volume > 100000000
- 1 day ago close * 1 day ago volume > 100000000
- [0] 30 minute sum( close ,  120 ) crossed above [-14] 30 minute max( 2000 ,  [0] 30 minute sum( close ,  120 ) ) * 0.9

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: money bump
Scan id: 10727075
Slug: money-bump
Source URL: https://chartink.com/screener/money-bump
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-01-05T10:34:54.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Disabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] [0] 30 minute count( 800, 1 where [0] 30 minute sum( close ,  120 ) < 200 ) > 600
    group_path: root/group[cash|all]
4. [Enabled] [0] 30 minute sum( close ,  120 ) crossed above 200
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
7. [Enabled] [0] 30 minute count( 800, 1 where [0] 30 minute sum( close ,  120 ) < 60 ) > 600
    group_path: root/group[cash|all]
8. [Enabled] [0] 30 minute sum( close ,  120 ) crossed above 85
    group_path: root/group[cash|all]
9. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
10. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
11. [Disabled] [0] 30 minute sum( close ,  120 ) crossed above [-14] 30 minute max( 800 ,  [0] 30 minute sum( close ,  120 ) ) * 1.5
    group_path: root/group[cash|all]
12. [Disabled] [0] 30 minute sum( close ,  120 ) crossed above [-100] 30 minute max( 800 ,  [0] 30 minute sum( close ,  120 ) ) * 3
    group_path: root/group[cash|all]
13. [Disabled] [0] 5 minute sum( close ,  120 ) crossed above [-100] 5 minute max( 800 ,  [0] 5 minute sum( close ,  120 ) ) * 3
    group_path: root/group[cash|all]
14. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
15. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
16. [Enabled] [0] 30 minute sum( close ,  120 ) crossed above [-14] 30 minute max( 2000 ,  [0] 30 minute sum( close ,  120 ) ) * 0.9
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( 1 day ago close * 1 day ago volume > 100000000 and [0] 30 minute sum( [0] 30 minute std( [0] 30 minute sma( [0] 30 minute close * [0] 30 minute volume , 10 ) / 10000000 , 14 ) , 120 ) > [-14] 30 minute max( 2000 , [0] 30 minute sum( [0] 30 minute std( [0] 30 minute sma( [0] 30 minute close * [0] 30 minute volume , 10 ) / 10000000 , 14 ) , 120 ) ) * 0.9 and [ -1 ] 30 minute sum( [0] 30 minute std( [0] 30 minute sma( [0] 30 minute close * [0] 30 minute volume , 10 ) / 10000000 , 14 ), 120 ) <= [ -15 ] 30 minute max( 2000 , [0] 30 minute sum( [0] 30 minute std( [0] 30 minute sma( [0] 30 minute close * [0] 30 minute volume , 10 ) / 10000000 , 14 ) , 120 ) )* 0.9 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Disabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|all] | [0] 30 minute count( 800, 1 where [0] 30 minute sum( close ,  120 ) < 200 ) > 600 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 4 | Enabled | root/group[cash\|all] | [0] 30 minute sum( close ,  120 ) crossed above 200 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 6 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 5 | 7 | Enabled | root/group[cash\|all] | [0] 30 minute count( 800, 1 where [0] 30 minute sum( close ,  120 ) < 60 ) > 600 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 8 | Enabled | root/group[cash\|all] | [0] 30 minute sum( close ,  120 ) crossed above 85 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 10 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 8 | 11 | Disabled | root/group[cash\|all] | [0] 30 minute sum( close ,  120 ) crossed above [-14] 30 minute max( 800 ,  [0] 30 minute sum( close ,  120 ) ) * 1.5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 12 | Disabled | root/group[cash\|all] | [0] 30 minute sum( close ,  120 ) crossed above [-100] 30 minute max( 800 ,  [0] 30 minute sum( close ,  120 ) ) * 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 13 | Disabled | root/group[cash\|all] | [0] 5 minute sum( close ,  120 ) crossed above [-100] 5 minute max( 800 ,  [0] 5 minute sum( close ,  120 ) ) * 3 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 11 | 15 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 12 | 16 | Enabled | root/group[cash\|all] | [0] 30 minute sum( close ,  120 ) crossed above [-14] 30 minute max( 2000 ,  [0] 30 minute sum( close ,  120 ) ) * 0.9 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `[0] 30 minute count( 800, 1 where [0] 30 minute sum( close ,  120 ) < 200 ) > 600` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `[0] 30 minute sum( close ,  120 ) crossed above 200` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#7** `[0] 30 minute count( 800, 1 where [0] 30 minute sum( close ,  120 ) < 60 ) > 600` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[0] 30 minute sum( close ,  120 ) crossed above 85` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#10** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#15** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#16** `[0] 30 minute sum( close ,  120 ) crossed above [-14] 30 minute max( 2000 ,  [0] 30 minute sum( close ,  120 ) ) * 0.9` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **4** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #2
- **Condition (verbatim):** `1 day ago close * 1 day ago volume > 100000000`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #11
- **Condition (verbatim):** `[0] 30 minute sum( close ,  120 ) crossed above [-14] 30 minute max( 800 ,  [0] 30 minute sum( close ,  120 ) ) * 1.5`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #12
- **Condition (verbatim):** `[0] 30 minute sum( close ,  120 ) crossed above [-100] 30 minute max( 800 ,  [0] 30 minute sum( close ,  120 ) ) * 3`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #13
- **Condition (verbatim):** `[0] 5 minute sum( close ,  120 ) crossed above [-100] 5 minute max( 800 ,  [0] 5 minute sum( close ,  120 ) ) * 3`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 16 time(s) in the expression tree
- `volume` — appears 16 time(s) in the expression tree
- `sum` — appears 12 time(s) in the expression tree
- `stddva` — appears 12 time(s) in the expression tree
- `sma` — appears 12 time(s) in the expression tree
- `max` — appears 4 time(s) in the expression tree
- `count` — appears 2 time(s) in the expression tree

### Operators observed
- `*` — 8 occurrence(s)
- `>` — 6 occurrence(s)
- `crossed above` — 6 occurrence(s)
- `<` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `30_minute`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volatility, Volume/delivery, Trend following, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **4** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Moving average, Volatility, Volume/delivery, Trend following, Momentum, Multi-factor
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, indicator:volume, indicator:sma, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

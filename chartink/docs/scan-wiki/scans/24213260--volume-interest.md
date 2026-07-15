---
scan_id: 24213260
scan_name: Volume Interest
source_url: https://chartink.com/screener/volume-interest-5
market: Indian equities
horizon: Multi-horizon
classification: ["Moving average", "Volume/delivery", "Trend following", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "universe:nifty-200", "indicator:volume", "indicator:sma", "timeframe:daily", "timeframe:monthly", "timeframe:weekly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# Volume Interest

## Source

- Chartink URL: https://chartink.com/screener/volume-interest-5
- Scan ID: `24213260`
- Slug: `volume-interest-5`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2025-10-20T05:57:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24213260.json](../source-snapshots/24213260.json)
- Text snapshot: [source-snapshots/24213260.txt](../source-snapshots/24213260.txt)

## What this scan is for

This is a **multi-horizon** screen over **nifty 200** with **6** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Moving average, Volume/delivery, Trend following, Momentum, Multi-factor**.
The active tests, in captured order, are:
- weekly volume crossed above 1 week ago sma( close ,  7 ) * 2.5
- daily volume crossed above 1 day ago max( 233 ,  daily volume ) * 0.9
- weekly volume crossed above 1 week ago max( 52 ,  weekly volume ) * 0.9
- daily volume crossed above 1 day ago max( 233 ,  daily volume )
- weekly volume crossed above 1 week ago max( 52 ,  weekly volume )
- daily volume > daily sma( close ,  20 ) * 3

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Volume Interest
Scan id: 24213260
Slug: volume-interest-5
Source URL: https://chartink.com/screener/volume-interest-5
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-10-20T05:57:56.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
2. [Disabled] daily volume crossed above 1 day ago sma( close ,  7 ) * 2.5
    group_path: root/group[cash|any]
3. [Enabled] weekly volume crossed above 1 week ago sma( close ,  7 ) * 2.5
    group_path: root/group[cash|any]
4. [Disabled] monthly volume crossed above 1 month ago sma( close ,  7 ) * 2
    group_path: root/group[cash|any]
5. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
6. [Enabled] daily volume crossed above 1 day ago max( 233 ,  daily volume ) * 0.9
    group_path: root/group[cash|any]
7. [Enabled] weekly volume crossed above 1 week ago max( 52 ,  weekly volume ) * 0.9
    group_path: root/group[cash|any]
8. [Disabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|any])
9. [Enabled] daily volume crossed above 1 day ago max( 233 ,  daily volume )
    group_path: root/group[cash|any]
10. [Enabled] weekly volume crossed above 1 week ago max( 52 ,  weekly volume )
    group_path: root/group[cash|any]
11. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
12. [Enabled] daily volume > daily sma( close ,  20 ) * 3
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( daily volume > daily sma( daily volume , 20 ) * 3 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Disabled | root/group[cash\|any] | daily volume crossed above 1 day ago sma( close ,  7 ) * 2.5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 2 | 3 | Enabled | root/group[cash\|any] | weekly volume crossed above 1 week ago sma( close ,  7 ) * 2.5 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. References weekly bars / weekly offset. |
| 3 | 4 | Disabled | root/group[cash\|any] | monthly volume crossed above 1 month ago sma( close ,  7 ) * 2 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. References monthly bars / monthly offset. |
| 4 | 6 | Enabled | root/group[cash\|any] | daily volume crossed above 1 day ago max( 233 ,  daily volume ) * 0.9 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. |
| 5 | 7 | Enabled | root/group[cash\|any] | weekly volume crossed above 1 week ago max( 52 ,  weekly volume ) * 0.9 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 6 | 9 | Enabled | root/group[cash\|any] | daily volume crossed above 1 day ago max( 233 ,  daily volume ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. |
| 7 | 10 | Enabled | root/group[cash\|any] | weekly volume crossed above 1 week ago max( 52 ,  weekly volume ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset. |
| 8 | 12 | Enabled | root/group[cash\|all] | daily volume > daily sma( close ,  20 ) * 3 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `weekly volume crossed above 1 week ago sma( close ,  7 ) * 2.5` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. References weekly bars / weekly offset.
- **#6** `daily volume crossed above 1 day ago max( 233 ,  daily volume ) * 0.9` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars.
- **#7** `weekly volume crossed above 1 week ago max( 52 ,  weekly volume ) * 0.9` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#9** `daily volume crossed above 1 day ago max( 233 ,  daily volume )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars.
- **#10** `weekly volume crossed above 1 week ago max( 52 ,  weekly volume )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Volume condition gates participation/liquidity. max(N, series) is the highest value of series over N bars. References weekly bars / weekly offset.
- **#12** `daily volume > daily sma( close ,  20 ) * 3` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #2
- **Condition (verbatim):** `daily volume crossed above 1 day ago sma( close ,  7 ) * 2.5`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #4
- **Condition (verbatim):** `monthly volume crossed above 1 month ago sma( close ,  7 ) * 2`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `volume` — appears 16 time(s) in the expression tree
- `sma` — appears 4 time(s) in the expression tree
- `max` — appears 4 time(s) in the expression tree

### Operators observed
- `crossed above` — 7 occurrence(s)
- `*` — 6 occurrence(s)
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
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `0_weeks_ago`, `1_days_ago`, `1_months_ago`, `1_weeks_ago`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery, Trend following, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Moving average, Volume/delivery, Trend following, Momentum, Multi-factor
- **Tags:** bias:upward-condition, universe:nifty-200, indicator:volume, indicator:sma, timeframe:daily, timeframe:monthly, timeframe:weekly
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 8920664
scan_name: acc dist second resistance daily
source_url: https://chartink.com/screener/acc-dist-second-resistance-daily
market: Indian equities
horizon: Multi-horizon
classification: ["Volume/delivery", "Breakout", "Momentum", "Multi-factor"]
tags: ["bias:upward-condition", "universe:nifty-50", "timeframe:daily", "timeframe:weekly", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 500
root_join: any
primary_classification: Volume/delivery
---

# acc dist second resistance daily

## Source

- Chartink URL: https://chartink.com/screener/acc-dist-second-resistance-daily
- Scan ID: `8920664`
- Slug: `acc-dist-second-resistance-daily`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2022-07-01T15:15:49.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8920664.json](../source-snapshots/8920664.json)
- Text snapshot: [source-snapshots/8920664.txt](../source-snapshots/8920664.txt)

## What this scan is for

This is a **multi-horizon** screen over **nifty 500** with **4** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Volume/delivery, Breakout, Momentum, Multi-factor**.
The active tests, in captured order, are:
- 1 day ago accdist + ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) crossed above daily accdist
- daily high > 1 day ago max( 21 ,  daily high )
- 1 week ago accdist + ( 1 week ago max( 21 ,  1 week ago accdist ) - 1 week ago min( 21 ,  1 week ago accdist ) ) crossed above weekly accdist
- daily high > 1 day ago max( 21 ,  daily high )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: acc dist second resistance daily
Scan id: 8920664
Slug: acc-dist-second-resistance-daily
Source URL: https://chartink.com/screener/acc-dist-second-resistance-daily
Root universe/segment: nifty 500
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-07-01T15:15:49.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago accdist + ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) crossed above daily accdist
    group_path: root/group[cash|all]
3. [Enabled] daily high > 1 day ago max( 21 ,  daily high )
    group_path: root/group[cash|all]
4. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] 1 week ago accdist + ( 1 week ago max( 21 ,  1 week ago accdist ) - 1 week ago min( 21 ,  1 week ago accdist ) ) crossed above weekly accdist
    group_path: root/group[cash|all]
6. [Enabled] daily high > 1 day ago max( 21 ,  daily high )
    group_path: root/group[cash|all]
7. [Disabled] [GROUP segment=nifty 500 join=all combination=passes measurevalue=default]  (path: root/group[nifty 500|all])
8. [Disabled] [-1] 60 minute accdist + ( [-1] 60 minute max( 28 ,  [0] 60 minute accdist ) - [-1] 60 minute min( 28 ,  [0] 60 minute accdist ) ) crossed above [0] 60 minute accdist
    group_path: root/group[nifty 500|all]
9. [Disabled] [-1] 120 minute accdist + ( [-1] 120 minute max( 21 ,  [0] 120 minute accdist ) - [-1] 120 minute min( 21 ,  [0] 120 minute accdist ) ) crossed above [0] 120 minute accdist
    group_path: root/group[nifty 500|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 500 ( ( cash ( 1 day ago accdist  + ( 1 day ago max( 21 , latest accdist  ) - 1 day ago min( 21 , latest accdist  ) ) > latest accdist  and 2 day ago  accdist  + ( 2 day ago  max( 21 , latest accdist  )- 2 day ago  min( 21 , latest accdist  )) <= 1 day ago  accdist  and latest high > 1 day ago max( 21 , latest high ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago accdist + ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) crossed above daily accdist | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily high > 1 day ago max( 21 ,  daily high ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. |
| 3 | 5 | Enabled | root/group[cash\|all] | 1 week ago accdist + ( 1 week ago max( 21 ,  1 week ago accdist ) - 1 week ago min( 21 ,  1 week ago accdist ) ) crossed above weekly accdist | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset. |
| 4 | 6 | Enabled | root/group[cash\|all] | daily high > 1 day ago max( 21 ,  daily high ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. |
| 5 | 8 | Disabled | root/group[nifty 500\|all] | [-1] 60 minute accdist + ( [-1] 60 minute max( 28 ,  [0] 60 minute accdist ) - [-1] 60 minute min( 28 ,  [0] 60 minute accdist ) ) crossed above [0] 60 minute accdist | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 9 | Disabled | root/group[nifty 500\|all] | [-1] 120 minute accdist + ( [-1] 120 minute max( 21 ,  [0] 120 minute accdist ) - [-1] 120 minute min( 21 ,  [0] 120 minute accdist ) ) crossed above [0] 120 minute accdist | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago accdist + ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) crossed above daily accdist` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#3** `daily high > 1 day ago max( 21 ,  daily high )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars.
- **#5** `1 week ago accdist + ( 1 week ago max( 21 ,  1 week ago accdist ) - 1 week ago min( 21 ,  1 week ago accdist ) ) crossed above weekly accdist` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. References weekly bars / weekly offset.
- **#6** `daily high > 1 day ago max( 21 ,  daily high )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #8
- **Condition (verbatim):** `[-1] 60 minute accdist + ( [-1] 60 minute max( 28 ,  [0] 60 minute accdist ) - [-1] 60 minute min( 28 ,  [0] 60 minute accdist ) ) crossed above [0] 60 minute accdist`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #9
- **Condition (verbatim):** `[-1] 120 minute accdist + ( [-1] 120 minute max( 21 ,  [0] 120 minute accdist ) - [-1] 120 minute min( 21 ,  [0] 120 minute accdist ) ) crossed above [0] 120 minute accdist`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `accdist` — appears 16 time(s) in the expression tree
- `max` — appears 6 time(s) in the expression tree
- `min` — appears 4 time(s) in the expression tree
- `high` — appears 4 time(s) in the expression tree

### Operators observed
- `+` — 4 occurrence(s)
- `crossed above` — 4 occurrence(s)
- `>` — 2 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **nifty 500**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_weeks_ago`, `120_minute`, `1_days_ago`, `1_weeks_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Breakout, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Volume/delivery, Breakout, Momentum, Multi-factor
- **Tags:** bias:upward-condition, universe:nifty-50, timeframe:daily, timeframe:weekly, timeframe:intraday-bars
- **Root universe:** nifty 500
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

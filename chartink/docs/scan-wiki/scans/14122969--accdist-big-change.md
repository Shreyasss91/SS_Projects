---
scan_id: 14122969
scan_name: ACC/DIST BIG CHANGE
source_url: https://chartink.com/screener/acc-dist-big-change
market: Indian equities
horizon: Intraday
classification: ["Volume/delivery", "Momentum"]
tags: ["bias:upward-condition", "universe:nifty-200", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: any
primary_classification: Volume/delivery
---

# ACC/DIST BIG CHANGE

## Source

- Chartink URL: https://chartink.com/screener/acc-dist-big-change
- Scan ID: `14122969`
- Slug: `acc-dist-big-change`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-12-09T04:31:06.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/14122969.json](../source-snapshots/14122969.json)
- Text snapshot: [source-snapshots/14122969.txt](../source-snapshots/14122969.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **3** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.
The active tests, in captured order, are:
- daily abs( daily accdist - 20 days ago accdist ) crossed above 3 days ago max( 120 ,  daily abs( daily accdist - 20 days ago accdist ) )
- daily abs( [0] 60 minute accdist - [-20] 60 minute accdist ) crossed above [-3] 60 minute max( 120 ,  [0] 60 minute abs( [0] 60 minute accdist - [-20] 60 minute accdist ) )
- daily abs( [0] 30 minute accdist - [-20] 30 minute accdist ) crossed above [-3] 30 minute max( 180 ,  [0] 30 minute abs( [0] 30 minute accdist - [-20] 30 minute accdist ) )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: ACC/DIST BIG CHANGE
Scan id: 14122969
Slug: acc-dist-big-change
Source URL: https://chartink.com/screener/acc-dist-big-change
Root universe/segment: nifty 200
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-12-09T04:31:06.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily abs( daily accdist - 20 days ago accdist ) crossed above 3 days ago max( 120 ,  daily abs( daily accdist - 20 days ago accdist ) )
2. [Enabled] daily abs( [0] 60 minute accdist - [-20] 60 minute accdist ) crossed above [-3] 60 minute max( 120 ,  [0] 60 minute abs( [0] 60 minute accdist - [-20] 60 minute accdist ) )
3. [Enabled] daily abs( [0] 30 minute accdist - [-20] 30 minute accdist ) crossed above [-3] 30 minute max( 180 ,  [0] 30 minute abs( [0] 30 minute accdist - [-20] 30 minute accdist ) )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( abs( latest accdist  - 20 days ago accdist  ) > 3 days ago max( 120 , abs( latest accdist  - 20 days ago accdist  ) ) and abs( 1 day ago  accdist  - 21 days ago  accdist  ) <= 4 days ago  max( 120 , abs( latest accdist  - 20 days ago accdist  ) ) or abs( [0] 1 hour accdist  - [-20] 1 hour accdist  ) > [-3] 1 hour max( 120 , abs( [0] 1 hour accdist  - [-20] 1 hour accdist  ) ) and abs( [ -1 ] 1 hour accdist  - [ -21 ] 1 hour accdist  ) <= [ -4 ] 1 hour max( 120 , abs( [0] 1 hour accdist  - [-20] 1 hour accdist  ) ) or abs( [0] 30 minute accdist  - [-20] 30 minute accdist  ) > [-3] 30 minute max( 180 , abs( [0] 30 minute accdist  - [-20] 30 minute accdist  ) ) and abs( [ -1 ] 30 minute accdist  - [ -21 ] 30 minute accdist  ) <= [ -4 ] 30 minute max( 180 , abs( [0] 30 minute accdist  - [-20] 30 minute accdist  ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily abs( daily accdist - 20 days ago accdist ) crossed above 3 days ago max( 120 ,  daily abs( daily accdist - 20 days ago accdist ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. |
| 2 | 2 | Enabled | root | daily abs( [0] 60 minute accdist - [-20] 60 minute accdist ) crossed above [-3] 60 minute max( 120 ,  [0] 60 minute abs( [0] 60 minute accdist - [-20] 60 minute accdist ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 3 | Enabled | root | daily abs( [0] 30 minute accdist - [-20] 30 minute accdist ) crossed above [-3] 30 minute max( 180 ,  [0] 30 minute abs( [0] 30 minute accdist - [-20] 30 minute accdist ) ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily abs( daily accdist - 20 days ago accdist ) crossed above 3 days ago max( 120 ,  daily abs( daily accdist - 20 days ago accdist ) )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars.
- **#2** `daily abs( [0] 60 minute accdist - [-20] 60 minute accdist ) crossed above [-3] 60 minute max( 120 ,  [0] 60 minute abs( [0] 60 minute accdist - [-20] 60 minute accdist ) )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#3** `daily abs( [0] 30 minute accdist - [-20] 30 minute accdist ) crossed above [-3] 30 minute max( 180 ,  [0] 30 minute abs( [0] 30 minute accdist - [-20] 30 minute accdist ) )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `accdist` — appears 12 time(s) in the expression tree
- `abs` — appears 6 time(s) in the expression tree
- `max` — appears 3 time(s) in the expression tree

### Operators observed
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
- Timeframe tokens: `0_days_ago`, `20_days_ago`, `30_minute`, `3_days_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Momentum
- **Tags:** bias:upward-condition, universe:nifty-200, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

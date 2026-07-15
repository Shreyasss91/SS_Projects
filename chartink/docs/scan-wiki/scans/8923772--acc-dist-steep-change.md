---
scan_id: 8923772
scan_name: acc dist steep change
source_url: https://chartink.com/screener/acc-dist-steep-change
market: Indian equities
horizon: Multi-horizon
classification: ["Volume/delivery", "Momentum"]
tags: ["universe:nifty-200", "timeframe:intraday-bars", "timeframe:monthly", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: any
primary_classification: Volume/delivery
---

# acc dist steep change

## Source

- Chartink URL: https://chartink.com/screener/acc-dist-steep-change
- Scan ID: `8923772`
- Slug: `acc-dist-steep-change`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2022-07-02T06:19:18.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8923772.json](../source-snapshots/8923772.json)
- Text snapshot: [source-snapshots/8923772.txt](../source-snapshots/8923772.txt)

## What this scan is for

This scan, titled "acc dist steep change", appears designed to screen Indian equities in the **nifty 200** universe using **5 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Multi-horizon**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 4_months_ago, 60_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: acc dist steep change
Scan id: 8923772
Slug: acc-dist-steep-change
Source URL: https://chartink.com/screener/acc-dist-steep-change
Root universe/segment: nifty 200
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-07-02T06:19:18.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago accdist + ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) crossed above daily accdist
    group_path: root/group[cash|all]
3. [Enabled] daily high > 1 day ago max( 21 ,  daily high )
    group_path: root/group[cash|all]
4. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] daily abs( daily accdist - 1 day ago accdist ) / daily abs( 1 day ago accdist ) * 1 > 0.4
    group_path: root/group[cash|all]
6. [Enabled] ( daily abs( daily accdist ) - daily abs( 1 day ago accdist ) ) / ( daily abs( 1 day ago accdist ) * 0.01 ) > 100
    group_path: root/group[cash|all]
7. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
8. [Enabled] [0] 60 minute accdist crossed below [-10] 60 minute min( 120 ,  [0] 60 minute accdist ) * 1
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( ( cash ( [0] 1 hour accdist  < [-10] 1 hour min( 120 , [0] 1 hour accdist  ) * 1 and [ -1 ] 1 hour accdist  >= [ -11 ] 1 hour min( 120 , [0] 1 hour accdist  )* 1 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 2 | Enabled | 1 day ago accdist + ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) crossed above daily accdist | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 3 | Enabled | daily high > 1 day ago max( 21 ,  daily high ) | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. |
| 4 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 5 | Enabled | daily abs( daily accdist - 1 day ago accdist ) / daily abs( 1 day ago accdist ) * 1 > 0.4 | Inequality test: left expression must be strictly greater than right. |
| 6 | Enabled | ( daily abs( daily accdist ) - daily abs( 1 day ago accdist ) ) / ( daily abs( 1 day ago accdist ) * 0.01 ) > 100 | Inequality test: left expression must be strictly greater than right. |
| 7 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 8 | Enabled | [0] 60 minute accdist crossed below [-10] 60 minute min( 120 ,  [0] 60 minute accdist ) * 1 | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago accdist + ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) crossed above daily accdist` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#3** `daily high > 1 day ago max( 21 ,  daily high )` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars.
- **#5** `daily abs( daily accdist - 1 day ago accdist ) / daily abs( 1 day ago accdist ) * 1 > 0.4` — Inequality test: left expression must be strictly greater than right.
- **#6** `( daily abs( daily accdist ) - daily abs( 1 day ago accdist ) ) / ( daily abs( 1 day ago accdist ) * 0.01 ) > 100` — Inequality test: left expression must be strictly greater than right.
- **#8** `[0] 60 minute accdist crossed below [-10] 60 minute min( 120 ,  [0] 60 minute accdist ) * 1` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `abs` — appears 5 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `min` — appears 2 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 3 occurrence(s)
- `/` — 2 occurrence(s)
- `*` — 2 occurrence(s)
- `+` — 1 occurrence(s)
- `crossed above` — 1 occurrence(s)
- `crossed below` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `4_months_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **5** active filters — transparent screening logic.
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

- **Horizon:** Multi-horizon
- **Methods:** Volume/delivery, Momentum
- **Tags:** universe:nifty-200, timeframe:intraday-bars, timeframe:monthly, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

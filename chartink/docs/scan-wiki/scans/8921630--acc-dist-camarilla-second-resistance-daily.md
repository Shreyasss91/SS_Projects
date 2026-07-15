---
scan_id: 8921630
scan_name: acc dist camarilla second resistance daily
source_url: https://chartink.com/screener/acc-dist-camarilla-second-resistance-daily
market: Indian equities
horizon: Swing
classification: ["Support/resistance", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:nifty-50", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 1
needs_review_filter_count: 0
root_segment: nifty 500
root_join: any
primary_classification: Support/resistance
---

# acc dist camarilla second resistance daily

## Source

- Chartink URL: https://chartink.com/screener/acc-dist-camarilla-second-resistance-daily
- Scan ID: `8921630`
- Slug: `acc-dist-camarilla-second-resistance-daily`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2022-07-01T17:33:14.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/8921630.json](../source-snapshots/8921630.json)
- Text snapshot: [source-snapshots/8921630.txt](../source-snapshots/8921630.txt)

## What this scan is for

This scan, titled "acc dist camarilla second resistance daily", appears designed to screen Indian equities in the **nifty 500** universe using **1 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Support/resistance, Volume/delivery, Momentum, Multi-factor**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: acc dist camarilla second resistance daily
Scan id: 8921630
Slug: acc-dist-camarilla-second-resistance-daily
Source URL: https://chartink.com/screener/acc-dist-camarilla-second-resistance-daily
Root universe/segment: nifty 500
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-07-01T17:33:14.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] ( ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) * 2.2 ) + 1 day ago accdist crossed above daily accdist
    group_path: root/group[cash|all]
3. [Disabled] daily high > 1 day ago max( 21 ,  daily high )
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 500 ( ( cash ( ( ( 1 day ago max( 21 , latest accdist  ) - 1 day ago min( 21 , latest accdist  ) ) * 2.2 ) + 1 day ago accdist  > latest accdist  and( ( 2 day ago  max( 21 , latest accdist  )- 2 day ago  min( 21 , latest accdist  )) * 2.2 ) + 2 day ago  accdist  <= 1 day ago  accdist  ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | ( ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) * 2.2 ) + 1 day ago accdist crossed above daily accdist | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 3 | Disabled | daily high > 1 day ago max( 21 ,  daily high ) | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `( ( 1 day ago max( 21 ,  daily accdist ) - 1 day ago min( 21 ,  daily accdist ) ) * 2.2 ) + 1 day ago accdist crossed above daily accdist` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **1** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily high > 1 day ago max( 21 ,  daily high )`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `accdist` — appears 4 time(s) in the expression tree
- `max` — appears 2 time(s) in the expression tree
- `high` — appears 2 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `+` — 1 occurrence(s)
- `crossed above` — 1 occurrence(s)
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
- Universe/segment: **nifty 500**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 500**. Liquidity and index membership still vary inside that set.
- **Method context:** Support/resistance, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **nifty 500**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **1** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Support/resistance, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:nifty-50, timeframe:daily
- **Root universe:** nifty 500
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

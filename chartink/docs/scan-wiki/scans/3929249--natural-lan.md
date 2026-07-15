---
scan_id: 3929249
scan_name: Natural lan
source_url: https://chartink.com/screener/natural-lan
market: Indian equities
horizon: Swing
classification: ["Volume/delivery", "Momentum"]
tags: ["universe:futures", "indicator:volume", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 1
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# Natural lan

## Source

- Chartink URL: https://chartink.com/screener/natural-lan
- Scan ID: `3929249`
- Slug: `natural-lan`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2021-02-11T02:43:34.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/3929249.json](../source-snapshots/3929249.json)
- Text snapshot: [source-snapshots/3929249.txt](../source-snapshots/3929249.txt)

## What this scan is for

This scan, titled "Natural lan", appears designed to screen Indian equities in the **futures** universe using **2 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Natural lan
Scan id: 3929249
Slug: natural-lan
Source URL: https://chartink.com/screener/natural-lan
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-02-11T02:43:34.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] daily close * daily volume > 100000000
2. [Enabled] [GROUP segment=futures join=any combination=passes measurevalue=default]  (path: root/group[futures|any])
3. [Enabled] daily ln_x crossed above 1 day ago min( 365 ,  daily ln_x )
    group_path: root/group[futures|any]
4. [Disabled] daily ln_x_accurate crossed above 1 day ago min( 365 ,  daily ln_x_accurate )
    group_path: root/group[futures|any]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( latest close * latest volume > 100000000 and( futures ( latest "2 * (  "(  "close" - 1 ) / (  "close" + 1 )" + ( 0.3333 *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" ) + ( 0.2 *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" ) )" > 1 day ago min( 365 , latest "2 * (  "(  "close" - 1 ) / (  "close" + 1 )" + ( 0.3333 *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" ) + ( 0.2 *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" ) )" ) and 1 day ago  "2 * (  "(  "close" - 1 ) / (  "close" + 1 )" + ( 0.3333 *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" ) + ( 0.2 *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" ) )" <= 2 day ago  min( 365 , latest "2 * (  "(  "close" - 1 ) / (  "close" + 1 )" + ( 0.3333 *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" ) + ( 0.2 *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" *  "(  "close" - 1 ) / (  "close" + 1 )" ) )" ) ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | daily close * daily volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | Enabled | [GROUP segment=futures join=any combination=passes measurevalue=default] | Nested group over segment **futures** with join **any** (combination=passes). Group status=Enabled. |
| 3 | Enabled | daily ln_x crossed above 1 day ago min( 365 ,  daily ln_x ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). min(N, series) is the lowest value of series over N bars. |
| 4 | Disabled | daily ln_x_accurate crossed above 1 day ago min( 365 ,  daily ln_x_accurate ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily close * daily volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `daily ln_x crossed above 1 day ago min( 365 ,  daily ln_x )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **1** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #4
- **Condition (verbatim):** `daily ln_x_accurate crossed above 1 day ago min( 365 ,  daily ln_x_accurate )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. min(N, series) is the lowest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `custom_indicator_13122` — appears 2 time(s) in the expression tree
- `min` — appears 2 time(s) in the expression tree
- `custom_indicator_13123` — appears 2 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 2 occurrence(s)
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
- Universe/segment: **futures**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Retains **1** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Volume/delivery, Momentum
- **Tags:** universe:futures, indicator:volume, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

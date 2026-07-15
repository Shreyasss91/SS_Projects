---
scan_id: 4781077
scan_name: Copy - Copy - RKB DARVAS BOX by AmitabhJha3
source_url: https://chartink.com/screener/copy-copy-rkb-darvas-box-by-amitabhjha3
market: Indian equities
horizon: Positional
classification: ["Oscillator", "Breakout"]
tags: ["bias:upward-condition", "universe:futures", "indicator:rsi", "timeframe:daily", "timeframe:monthly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Oscillator
---

# Copy - Copy - RKB DARVAS BOX by AmitabhJha3

## Source

- Chartink URL: https://chartink.com/screener/copy-copy-rkb-darvas-box-by-amitabhjha3
- Scan ID: `4781077`
- Slug: `copy-copy-rkb-darvas-box-by-amitabhjha3`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Positional
- Created at (Chartink): 2021-06-02T17:28:21.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/4781077.json](../source-snapshots/4781077.json)
- Text snapshot: [source-snapshots/4781077.txt](../source-snapshots/4781077.txt)

## What this scan is for

This is a **positional** screen over **futures** with **4** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Oscillator, Breakout**.
The active tests, in captured order, are:
- daily earning per share > daily p earning per share
- daily rsi( 14 ) > 60
- daily high = daily max( 3 ,  daily high )
- daily high > 1 month ago max( 12 ,  monthly high ) * 0.99

Author description (source metadata): Darvas Strategy

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - Copy - RKB DARVAS BOX by AmitabhJha3
Scan id: 4781077
Slug: copy-copy-rkb-darvas-box-by-amitabhjha3
Source URL: https://chartink.com/screener/copy-copy-rkb-darvas-box-by-amitabhjha3
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2021-06-02T17:28:21.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily earning per share > daily p earning per share
2. [Enabled] daily rsi( 14 ) > 60
3. [Enabled] daily high = daily max( 3 ,  daily high )
4. [Disabled] monthly high = monthly max( 12 ,  monthly high )
5. [Disabled] daily high = daily max( 250 ,  daily high )
6. [Enabled] daily high > 1 month ago max( 12 ,  monthly high ) * 0.99

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( earning per share[eps] > prev year eps and latest rsi( 14 ) > 60 and latest high = latest max( 3 , latest high ) and latest high > 1 month ago max( 12 , monthly high ) * 0.99 ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily earning per share > daily p earning per share | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | daily rsi( 14 ) > 60 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |
| 3 | 3 | Enabled | root | daily high = daily max( 3 ,  daily high ) | Equality test between left and right expressions. max(N, series) is the highest value of series over N bars. |
| 4 | 4 | Disabled | root | monthly high = monthly max( 12 ,  monthly high ) | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. References monthly bars / monthly offset. |
| 5 | 5 | Disabled | root | daily high = daily max( 250 ,  daily high ) | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 6 | 6 | Enabled | root | daily high > 1 month ago max( 12 ,  monthly high ) * 0.99 | Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. References monthly bars / monthly offset. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily earning per share > daily p earning per share` — Inequality test: left expression must be strictly greater than right.
- **#2** `daily rsi( 14 ) > 60` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.
- **#3** `daily high = daily max( 3 ,  daily high )` — Equality test between left and right expressions. max(N, series) is the highest value of series over N bars.
- **#6** `daily high > 1 month ago max( 12 ,  monthly high ) * 0.99` — Inequality test: left expression must be strictly greater than right. max(N, series) is the highest value of series over N bars. References monthly bars / monthly offset.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #4
- **Condition (verbatim):** `monthly high = monthly max( 12 ,  monthly high )`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily high = daily max( 250 ,  daily high )`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `high` — appears 8 time(s) in the expression tree
- `max` — appears 4 time(s) in the expression tree
- `earning per share` — appears 1 time(s) in the expression tree
- `p earning per share` — appears 1 time(s) in the expression tree
- `rsi` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 3 occurrence(s)
- `=` — 3 occurrence(s)
- `*` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `1_months_ago`

## How to use it

- **Horizon context:** treat as **Positional** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Breakout.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Positional
- **Methods:** Oscillator, Breakout
- **Tags:** bias:upward-condition, universe:futures, indicator:rsi, timeframe:daily, timeframe:monthly
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

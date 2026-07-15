---
scan_id: 25165131
scan_name: Volume Profile
source_url: https://chartink.com/screener/volume-profile-137
market: Indian equities
horizon: Positional
classification: ["Momentum"]
tags: ["bias:downward-condition", "universe:nifty-200", "timeframe:daily", "timeframe:monthly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 1
disabled_filter_count: 5
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Momentum
---

# Volume Profile

## Source

- Chartink URL: https://chartink.com/screener/volume-profile-137
- Scan ID: `25165131`
- Slug: `volume-profile-137`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Positional
- Created at (Chartink): 2026-01-24T14:02:55.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/25165131.json](../source-snapshots/25165131.json)
- Text snapshot: [source-snapshots/25165131.txt](../source-snapshots/25165131.txt)

## What this scan is for

This is a **positional** screen over **nifty 200** with **1** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Momentum**.
The active tests, in captured order, are:
- daily xpress indicator 3025 val( hlc3 ) crossed below daily close

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Volume Profile
Scan id: 25165131
Slug: volume-profile-137
Source URL: https://chartink.com/screener/volume-profile-137
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2026-01-24T14:02:55.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] daily high crossed above 1 month ago xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  200 )
2. [Disabled] daily high crossed above 20 days ago xpress indicator 207 basis( 20 )
3. [Disabled] daily % change > 1
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Disabled] daily high crossed above daily xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  40 )
    group_path: root/group[cash|all]
6. [Disabled] 1 day ago count( 5, 1 where daily high < daily xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  40 ) ) < 1
    group_path: root/group[cash|all]
7. [Enabled] daily xpress indicator 3025 val( hlc3 ) crossed below daily close

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 (  daily ^3025('src'=' daily "high+low+close/3"','output'='val')^ <  daily close and  1 day ago  ^3025('src'=' daily "high+low+close/3"','output'='val')^ >=  1 day ago  close ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Disabled | root | daily high crossed above 1 month ago xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  200 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset. |
| 2 | 2 | Disabled | root | daily high crossed above 20 days ago xpress indicator 207 basis( 20 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 3 | 3 | Disabled | root | daily % change > 1 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. |
| 4 | 5 | Disabled | root/group[cash\|all] | daily high crossed above daily xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  40 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. |
| 5 | 6 | Disabled | root/group[cash\|all] | 1 day ago count( 5, 1 where daily high < daily xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  40 ) ) < 1 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 6 | 7 | Enabled | root | daily xpress indicator 3025 val( hlc3 ) crossed below daily close | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **1** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#7** `daily xpress indicator 3025 val( hlc3 ) crossed below daily close` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar).

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **5** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily high crossed above 1 month ago xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  200 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. References monthly bars / monthly offset.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `daily high crossed above 20 days ago xpress indicator 207 basis( 20 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `daily % change > 1`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily high crossed above daily xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  40 )`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #6
- **Condition (verbatim):** `1 day ago count( 5, 1 where daily high < daily xpress indicator 1750 val( 200 ,  Both ,  20 ,  70 ,  40 ) ) < 1`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `high` — appears 4 time(s) in the expression tree
- `xpress indicator 1750 val` — appears 3 time(s) in the expression tree
- `enum` — appears 3 time(s) in the expression tree
- `xpress indicator 207 basis` — appears 1 time(s) in the expression tree
- `% change` — appears 1 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree
- `xpress indicator 3025 val` — appears 1 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `hlc3` — appears 1 time(s) in the expression tree

### Operators observed
- `crossed above` — 3 occurrence(s)
- `<` — 2 occurrence(s)
- `>` — 1 occurrence(s)
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
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `1_months_ago`, `20_days_ago`

## How to use it

- **Horizon context:** treat as **Positional** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **1** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **5** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Positional
- **Methods:** Momentum
- **Tags:** bias:downward-condition, universe:nifty-200, timeframe:daily, timeframe:monthly
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 11388421
scan_name: STRONG PRICE REJECTIONS_index
source_url: https://chartink.com/screener/test-2023-03-31-11
market: Indian equities
horizon: Swing
classification: ["Other"]
tags: ["universe:index", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 2
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: NIFTY_INDEX
root_join: any
primary_classification: Other
---

# STRONG PRICE REJECTIONS_index

## Source

- Chartink URL: https://chartink.com/screener/test-2023-03-31-11
- Scan ID: `11388421`
- Slug: `test-2023-03-31-11`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2023-03-31T11:47:04.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/11388421.json](../source-snapshots/11388421.json)
- Text snapshot: [source-snapshots/11388421.txt](../source-snapshots/11388421.txt)

## What this scan is for

This scan, titled "STRONG PRICE REJECTIONS_index", appears designed to screen Indian equities in the **NIFTY_INDEX** universe using **2 enabled** condition(s) combined with root join **any (OR)**.

Dominant method tag(s) inferred from conditions: **Other**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: STRONG PRICE REJECTIONS_index
Scan id: 11388421
Slug: test-2023-03-31-11
Source URL: https://chartink.com/screener/test-2023-03-31-11
Root universe/segment: NIFTY_INDEX
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-03-31T11:47:04.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily high - daily greatest > 125
    group_path: root/group[cash|all]
3. [Disabled] daily low - daily least < -125
    group_path: root/group[cash|all]
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Disabled] daily high - daily greatest = daily max( 30 ,  daily high - daily greatest )
    group_path: root/group[cash|all]
6. [Enabled] daily low - daily least = daily min( 30 ,  daily low - daily least )
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty_index ( ( cash ( latest low - least(  latest open, latest close  ) = latest min( 30 , latest low - least(  latest open, latest close  ) ) ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 2 | Enabled | daily high - daily greatest > 125 | Inequality test: left expression must be strictly greater than right. |
| 3 | Disabled | daily low - daily least < -125 | Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs. |
| 4 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 5 | Disabled | daily high - daily greatest = daily max( 30 ,  daily high - daily greatest ) | Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars. |
| 6 | Enabled | daily low - daily least = daily min( 30 ,  daily low - daily least ) | Equality test between left and right expressions. min(N, series) is the lowest value of series over N bars. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **2** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily high - daily greatest > 125` — Inequality test: left expression must be strictly greater than right.
- **#6** `daily low - daily least = daily min( 30 ,  daily low - daily least )` — Equality test between left and right expressions. min(N, series) is the lowest value of series over N bars.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #3
- **Condition (verbatim):** `daily low - daily least < -125`
- **Meaning:** Inequality test: left expression must be strictly less than right. Currently disabled in source — not applied when the scan runs.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #5
- **Condition (verbatim):** `daily high - daily greatest = daily max( 30 ,  daily high - daily greatest )`
- **Meaning:** Equality test between left and right expressions. Currently disabled in source — not applied when the scan runs. max(N, series) is the highest value of series over N bars.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `open` — appears 6 time(s) in the expression tree
- `close` — appears 6 time(s) in the expression tree
- `high` — appears 3 time(s) in the expression tree
- `greatest` — appears 3 time(s) in the expression tree
- `low` — appears 3 time(s) in the expression tree
- `least` — appears 3 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree

### Operators observed
- `-` — 4 occurrence(s)
- `=` — 2 occurrence(s)
- `>` — 1 occurrence(s)
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
- Universe/segment: **NIFTY_INDEX**
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **NIFTY_INDEX**. Liquidity and index membership still vary inside that set.
- **Method context:** Other.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **2** active filters — transparent screening logic.
- Universe pinned to **NIFTY_INDEX**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Other
- **Tags:** universe:index, timeframe:daily
- **Root universe:** NIFTY_INDEX
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

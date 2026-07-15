---
scan_id: 1434163
scan_name: "Jega's 20D BB Brk-up/down consol chk"
source_url: https://chartink.com/screener/copy-jega-s-20d-bb-brk-up-down-consol-chk
market: Indian equities
horizon: Swing
classification: ["Volatility", "Momentum"]
tags: ["universe:futures", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volatility
---

# Jega's 20D BB Brk-up/down consol chk

## Source

- Chartink URL: https://chartink.com/screener/copy-jega-s-20d-bb-brk-up-down-consol-chk
- Scan ID: `1434163`
- Slug: `copy-jega-s-20d-bb-brk-up-down-consol-chk`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2019-11-19T13:39:03.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1434163.json](../source-snapshots/1434163.json)
- Text snapshot: [source-snapshots/1434163.txt](../source-snapshots/1434163.txt)

## What this scan is for

This scan, titled "Jega's 20D BB Brk-up/down consol chk", appears designed to screen Indian equities in the **futures** universe using **4 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Volatility, Momentum**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 20_days_ago`.

Author description (source metadata): Trading

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Jega's 20D BB Brk-up/down consol chk
Scan id: 1434163
Slug: copy-jega-s-20d-bb-brk-up-down-consol-chk
Source URL: https://chartink.com/screener/copy-jega-s-20d-bb-brk-up-down-consol-chk
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-19T13:39:03.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|all])
2. [Enabled] daily close <= 20 days ago close * 1.013
    group_path: root/group[futures|all]
3. [Enabled] daily close >= 20 days ago close * .987
    group_path: root/group[futures|all]
4. [Enabled] [GROUP segment=futures join=any combination=passes measurevalue=default]  (path: root/group[futures|any])
5. [Enabled] 20 days ago close crossed below 20 days ago upper bollinger band( 20,2 )
    group_path: root/group[futures|any]
6. [Enabled] 20 days ago close crossed above 20 days ago upper bollinger band( 20,2 )
    group_path: root/group[futures|any]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( futures ( ( futures ( latest close <= 20 days ago close * 1.013 and latest close >= 20 days ago close * .987 ) ) and( futures ( 20 days ago close < 20 days ago upper bollinger band( 20,2 ) and 21 days ago  close >= 21 days ago  upper bollinger band( 20,2 ) or 20 days ago close > 20 days ago upper bollinger band( 20,2 ) and 21 days ago  close <= 21 days ago  upper bollinger band( 20,2 ) ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=futures join=all combination=passes measurevalue=default] | Nested group over segment **futures** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | daily close <= 20 days ago close * 1.013 | Inequality test: left expression must be less than or equal to right. |
| 3 | Enabled | daily close >= 20 days ago close * .987 | Inequality test: left expression must be greater than or equal to right. |
| 4 | Enabled | [GROUP segment=futures join=any combination=passes measurevalue=default] | Nested group over segment **futures** with join **any** (combination=passes). Group status=Enabled. |
| 5 | Enabled | 20 days ago close crossed below 20 days ago upper bollinger band( 20,2 ) | Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Bollinger fields are typically a moving average ± standard-deviation bands. |
| 6 | Enabled | 20 days ago close crossed above 20 days ago upper bollinger band( 20,2 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Bollinger fields are typically a moving average ± standard-deviation bands. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily close <= 20 days ago close * 1.013` — Inequality test: left expression must be less than or equal to right.
- **#3** `daily close >= 20 days ago close * .987` — Inequality test: left expression must be greater than or equal to right.
- **#5** `20 days ago close crossed below 20 days ago upper bollinger band( 20,2 )` — Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar). Bollinger fields are typically a moving average ± standard-deviation bands.
- **#6** `20 days ago close crossed above 20 days ago upper bollinger band( 20,2 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Bollinger fields are typically a moving average ± standard-deviation bands.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `close` — appears 6 time(s) in the expression tree
- `upper bollinger band` — appears 2 time(s) in the expression tree

### Operators observed
- `*` — 2 occurrence(s)
- `<=` — 1 occurrence(s)
- `>=` — 1 occurrence(s)
- `crossed below` — 1 occurrence(s)
- `crossed above` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `20_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volatility, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volatility, Momentum
- **Tags:** universe:futures, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

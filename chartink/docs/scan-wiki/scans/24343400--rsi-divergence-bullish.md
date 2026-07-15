---
scan_id: 24343400
scan_name: RSI DIVERGENCE BULLISH
source_url: https://chartink.com/screener/rsi-divergence-47474749
market: Indian equities
horizon: Intraday
classification: ["Oscillator"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:nifty-200", "indicator:rsi", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 8
disabled_filter_count: 2
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Oscillator
---

# RSI DIVERGENCE BULLISH

## Source

- Chartink URL: https://chartink.com/screener/rsi-divergence-47474749
- Scan ID: `24343400`
- Slug: `rsi-divergence-47474749`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2025-11-01T13:07:32.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24343400.json](../source-snapshots/24343400.json)
- Text snapshot: [source-snapshots/24343400.txt](../source-snapshots/24343400.txt)

## What this scan is for

This is a **intraday** screen over **nifty 200** with **8** active leaf condition(s) under root join **all (AND)**.
Its method labels are derived only from active expressions: **Oscillator**.
The active tests, in captured order, are:
- daily min( 8 ,  daily rsi( 14 ) ) > daily min( 21 ,  daily rsi( 14 ) ) * 1.2
- daily min( 8 ,  daily close ) < 8 days ago min( 21 ,  daily close )
- 1 day ago min( 8 ,  daily rsi( 14 ) ) <= 1 day ago min( 21 ,  daily rsi( 14 ) ) * 1.2
- 1 day ago min( 8 ,  daily close ) >= 9 days ago min( 21 ,  daily close )
- [0] 60 minute min( 8 ,  [0] 60 minute rsi( 14 ) ) > [0] 60 minute min( 21 ,  [0] 60 minute rsi( 14 ) ) * 1.2
- [0] 60 minute min( 8 ,  [0] 60 minute close ) < [-8] 60 minute min( 21 ,  [0] 60 minute close )
- [-1] 60 minute min( 8 ,  [0] 60 minute rsi( 14 ) ) <= [-1] 60 minute min( 21 ,  [0] 60 minute rsi( 14 ) ) * 1.2
- [-1] 60 minute min( 8 ,  [0] 60 minute close ) >= [-9] 60 minute min( 21 ,  [0] 60 minute close )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: RSI DIVERGENCE BULLISH
Scan id: 24343400
Slug: rsi-divergence-47474749
Source URL: https://chartink.com/screener/rsi-divergence-47474749
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-01T13:07:32.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all])
3. [Enabled] daily min( 8 ,  daily rsi( 14 ) ) > daily min( 21 ,  daily rsi( 14 ) ) * 1.2
    group_path: root/group[cash|all]/group[cash|all]
4. [Enabled] daily min( 8 ,  daily close ) < 8 days ago min( 21 ,  daily close )
    group_path: root/group[cash|all]/group[cash|all]
5. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any])
6. [Enabled] 1 day ago min( 8 ,  daily rsi( 14 ) ) <= 1 day ago min( 21 ,  daily rsi( 14 ) ) * 1.2
    group_path: root/group[cash|all]/group[cash|any]
7. [Enabled] 1 day ago min( 8 ,  daily close ) >= 9 days ago min( 21 ,  daily close )
    group_path: root/group[cash|all]/group[cash|any]
8. [Disabled] daily rsi( 14 ) > 30
    group_path: root/group[cash|all]
9. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
10. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|all])
11. [Enabled] [0] 60 minute min( 8 ,  [0] 60 minute rsi( 14 ) ) > [0] 60 minute min( 21 ,  [0] 60 minute rsi( 14 ) ) * 1.2
    group_path: root/group[cash|all]/group[cash|all]
12. [Enabled] [0] 60 minute min( 8 ,  [0] 60 minute close ) < [-8] 60 minute min( 21 ,  [0] 60 minute close )
    group_path: root/group[cash|all]/group[cash|all]
13. [Enabled] [GROUP segment=cash join=any combination=passes measurevalue=default]  (path: root/group[cash|all]/group[cash|any])
14. [Enabled] [-1] 60 minute min( 8 ,  [0] 60 minute rsi( 14 ) ) <= [-1] 60 minute min( 21 ,  [0] 60 minute rsi( 14 ) ) * 1.2
    group_path: root/group[cash|all]/group[cash|any]
15. [Enabled] [-1] 60 minute min( 8 ,  [0] 60 minute close ) >= [-9] 60 minute min( 21 ,  [0] 60 minute close )
    group_path: root/group[cash|all]/group[cash|any]
16. [Disabled] [0] 60 minute rsi( 14 ) > 30
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( nifty 200 ( ( cash ( ( cash ( [0] 1 hour min( 8 , [0] 1 hour rsi( 14 ) ) > [0] 1 hour min( 21 , [0] 1 hour rsi( 14 ) ) * 1.2 and [0] 1 hour min( 8 , [0] 1 hour close ) < [-8] 1 hour min( 21 , [0] 1 hour close ) ) ) and( cash ( [-1] 1 hour min( 8 , [0] 1 hour rsi( 14 ) ) <= [-1] 1 hour min( 21 , [0] 1 hour rsi( 14 ) ) * 1.2 or [-1] 1 hour min( 8 , [0] 1 hour close ) >= [-9] 1 hour min( 21 , [0] 1 hour close ) ) ) ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 3 | Enabled | root/group[cash\|all]/group[cash\|all] | daily min( 8 ,  daily rsi( 14 ) ) > daily min( 21 ,  daily rsi( 14 ) ) * 1.2 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. min(N, series) is the lowest value of series over N bars. |
| 2 | 4 | Enabled | root/group[cash\|all]/group[cash\|all] | daily min( 8 ,  daily close ) < 8 days ago min( 21 ,  daily close ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. |
| 3 | 6 | Enabled | root/group[cash\|all]/group[cash\|any] | 1 day ago min( 8 ,  daily rsi( 14 ) ) <= 1 day ago min( 21 ,  daily rsi( 14 ) ) * 1.2 | Inequality test: left expression must be less than or equal to right. RSI is a momentum oscillator from average gains/losses over its period. min(N, series) is the lowest value of series over N bars. |
| 4 | 7 | Enabled | root/group[cash\|all]/group[cash\|any] | 1 day ago min( 8 ,  daily close ) >= 9 days ago min( 21 ,  daily close ) | Inequality test: left expression must be greater than or equal to right. min(N, series) is the lowest value of series over N bars. |
| 5 | 8 | Disabled | root/group[cash\|all] | daily rsi( 14 ) > 30 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. |
| 6 | 11 | Enabled | root/group[cash\|all]/group[cash\|all] | [0] 60 minute min( 8 ,  [0] 60 minute rsi( 14 ) ) > [0] 60 minute min( 21 ,  [0] 60 minute rsi( 14 ) ) * 1.2 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | 12 | Enabled | root/group[cash\|all]/group[cash\|all] | [0] 60 minute min( 8 ,  [0] 60 minute close ) < [-8] 60 minute min( 21 ,  [0] 60 minute close ) | Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 8 | 14 | Enabled | root/group[cash\|all]/group[cash\|any] | [-1] 60 minute min( 8 ,  [0] 60 minute rsi( 14 ) ) <= [-1] 60 minute min( 21 ,  [0] 60 minute rsi( 14 ) ) * 1.2 | Inequality test: left expression must be less than or equal to right. RSI is a momentum oscillator from average gains/losses over its period. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 9 | 15 | Enabled | root/group[cash\|all]/group[cash\|any] | [-1] 60 minute min( 8 ,  [0] 60 minute close ) >= [-9] 60 minute min( 21 ,  [0] 60 minute close ) | Inequality test: left expression must be greater than or equal to right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 10 | 16 | Disabled | root/group[cash\|all] | [0] 60 minute rsi( 14 ) > 30 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **8** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `daily min( 8 ,  daily rsi( 14 ) ) > daily min( 21 ,  daily rsi( 14 ) ) * 1.2` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. min(N, series) is the lowest value of series over N bars.
- **#4** `daily min( 8 ,  daily close ) < 8 days ago min( 21 ,  daily close )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars.
- **#6** `1 day ago min( 8 ,  daily rsi( 14 ) ) <= 1 day ago min( 21 ,  daily rsi( 14 ) ) * 1.2` — Inequality test: left expression must be less than or equal to right. RSI is a momentum oscillator from average gains/losses over its period. min(N, series) is the lowest value of series over N bars.
- **#7** `1 day ago min( 8 ,  daily close ) >= 9 days ago min( 21 ,  daily close )` — Inequality test: left expression must be greater than or equal to right. min(N, series) is the lowest value of series over N bars.
- **#11** `[0] 60 minute min( 8 ,  [0] 60 minute rsi( 14 ) ) > [0] 60 minute min( 21 ,  [0] 60 minute rsi( 14 ) ) * 1.2` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#12** `[0] 60 minute min( 8 ,  [0] 60 minute close ) < [-8] 60 minute min( 21 ,  [0] 60 minute close )` — Inequality test: left expression must be strictly less than right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#14** `[-1] 60 minute min( 8 ,  [0] 60 minute rsi( 14 ) ) <= [-1] 60 minute min( 21 ,  [0] 60 minute rsi( 14 ) ) * 1.2` — Inequality test: left expression must be less than or equal to right. RSI is a momentum oscillator from average gains/losses over its period. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#15** `[-1] 60 minute min( 8 ,  [0] 60 minute close ) >= [-9] 60 minute min( 21 ,  [0] 60 minute close )` — Inequality test: left expression must be greater than or equal to right. min(N, series) is the lowest value of series over N bars. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **2** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #8
- **Condition (verbatim):** `daily rsi( 14 ) > 30`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #16
- **Condition (verbatim):** `[0] 60 minute rsi( 14 ) > 30`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `min` — appears 16 time(s) in the expression tree
- `rsi` — appears 10 time(s) in the expression tree
- `close` — appears 8 time(s) in the expression tree

### Operators observed
- `>` — 4 occurrence(s)
- `*` — 4 occurrence(s)
- `<` — 2 occurrence(s)
- `<=` — 2 occurrence(s)
- `>=` — 2 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `60_minute`, `8_days_ago`, `9_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **8** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Retains **2** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Oscillator
- **Tags:** bias:upward-condition, bias:downward-condition, universe:nifty-200, indicator:rsi, timeframe:daily, timeframe:intraday-bars
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

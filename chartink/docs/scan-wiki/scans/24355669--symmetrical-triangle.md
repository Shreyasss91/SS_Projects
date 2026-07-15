---
scan_id: 24355669
scan_name: Symmetrical Triangle
source_url: https://chartink.com/screener/symmetrical-triangle-266
market: Indian equities
horizon: Intraday
classification: ["Oscillator", "Price action", "Momentum", "Multi-factor"]
tags: ["universe:nifty-200", "indicator:stochastic", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 3
disabled_filter_count: 3
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Oscillator
---

# Symmetrical Triangle

## Source

- Chartink URL: https://chartink.com/screener/symmetrical-triangle-266
- Scan ID: `24355669`
- Slug: `symmetrical-triangle-266`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2025-11-02T14:23:13.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24355669.json](../source-snapshots/24355669.json)
- Text snapshot: [source-snapshots/24355669.txt](../source-snapshots/24355669.txt)

## What this scan is for

This scan, titled "Symmetrical Triangle", appears designed to screen Indian equities in the **nifty 200** universe using **3 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Oscillator, Price action, Momentum, Multi-factor**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 30_minute`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: Symmetrical Triangle
Scan id: 24355669
Slug: symmetrical-triangle-266
Source URL: https://chartink.com/screener/symmetrical-triangle-266
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-02T14:23:13.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] daily count( 15, 1 where daily count( 2, 1 where daily fast stochastic %d( 233 ,  3 ) - 1 day ago fast stochastic %d( 233 ,  3 ) > 0 ) = 1 ) >= 10
2. [Disabled] daily count( 2, 1 where daily fast stochastic %d( 233 ,  3 ) - 1 day ago fast stochastic %d( 233 ,  3 ) > 0 ) = 1
3. [Disabled] [0] 30 minute count( 15, 1 where [0] 30 minute count( 2, 1 where [0] 30 minute fast stochastic %d( 233 ,  3 ) - [-1] 30 minute fast stochastic %d( 233 ,  3 ) > 0 ) = 1 ) crossed above 10
4. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
5. [Enabled] [0] 30 minute sum( close ,  33 ) > -0.2
    group_path: root/group[cash|all]
6. [Enabled] [0] 30 minute sum( close ,  33 ) < 0.2
    group_path: root/group[cash|all]
7. [Enabled] [0] 30 minute fast stochastic %d( 233 ,  3 ) < 20
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( ( cash ( [0] 30 minute sum( [0] 30 minute fast stochastic %d( 233 , 3 ) - [-1] 30 minute fast stochastic %d( 233 , 3 ) , 33 ) > -0.2 and [0] 30 minute sum( [0] 30 minute fast stochastic %d( 233 , 3 ) - [-1] 30 minute fast stochastic %d( 233 , 3 ) , 33 ) < 0.2 and [0] 30 minute fast stochastic %d( 233 , 3 ) < 20 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | daily count( 15, 1 where daily count( 2, 1 where daily fast stochastic %d( 233 ,  3 ) - 1 day ago fast stochastic %d( 233 ,  3 ) > 0 ) = 1 ) >= 10 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Stochastic compares close location within a high-low range over its lookback. |
| 2 | Disabled | daily count( 2, 1 where daily fast stochastic %d( 233 ,  3 ) - 1 day ago fast stochastic %d( 233 ,  3 ) > 0 ) = 1 | Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Stochastic compares close location within a high-low range over its lookback. |
| 3 | Disabled | [0] 30 minute count( 15, 1 where [0] 30 minute count( 2, 1 where [0] 30 minute fast stochastic %d( 233 ,  3 ) - [-1] 30 minute fast stochastic %d( 233 ,  3 ) > 0 ) = 1 ) crossed above 10 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 5 | Enabled | [0] 30 minute sum( close ,  33 ) > -0.2 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | Enabled | [0] 30 minute sum( close ,  33 ) < 0.2 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | Enabled | [0] 30 minute fast stochastic %d( 233 ,  3 ) < 20 | Inequality test: left expression must be strictly less than right. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **3** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#5** `[0] 30 minute sum( close ,  33 ) > -0.2` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[0] 30 minute sum( close ,  33 ) < 0.2` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[0] 30 minute fast stochastic %d( 233 ,  3 ) < 20` — Inequality test: left expression must be strictly less than right. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data.

Combined effect:
- With root join **all**, the scan is more selective (intersection of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

There are **3** disabled leaf condition(s). Reasons for disabling are **not stated in source metadata** unless the description says so; the notes below are inference about what enabling each would do.

### Disabled #1
- **Condition (verbatim):** `daily count( 15, 1 where daily count( 2, 1 where daily fast stochastic %d( 233 ,  3 ) - 1 day ago fast stochastic %d( 233 ,  3 ) > 0 ) = 1 ) >= 10`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Stochastic compares close location within a high-low range over its lookback.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #2
- **Condition (verbatim):** `daily count( 2, 1 where daily fast stochastic %d( 233 ,  3 ) - 1 day ago fast stochastic %d( 233 ,  3 ) > 0 ) = 1`
- **Meaning:** Inequality test: left expression must be strictly greater than right. Currently disabled in source — not applied when the scan runs. Stochastic compares close location within a high-low range over its lookback.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.

### Disabled #3
- **Condition (verbatim):** `[0] 30 minute count( 15, 1 where [0] 30 minute count( 2, 1 where [0] 30 minute fast stochastic %d( 233 ,  3 ) - [-1] 30 minute fast stochastic %d( 233 ,  3 ) > 0 ) = 1 ) crossed above 10`
- **Meaning:** Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Currently disabled in source — not applied when the scan runs. Stochastic compares close location within a high-low range over its lookback. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), likely changing candidate count and timing.
- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; keeping it disabled preserves a wider (or differently timed) set of results.


## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `fast stochastic %d` — appears 11 time(s) in the expression tree
- `count` — appears 5 time(s) in the expression tree
- `sum` — appears 2 time(s) in the expression tree

### Operators observed
- `>` — 4 occurrence(s)
- `=` — 3 occurrence(s)
- `-` — 3 occurrence(s)
- `<` — 2 occurrence(s)
- `>=` — 1 occurrence(s)
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
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `30_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Price action, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **3** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Retains **3** disabled filter(s) in source — useful experimental toggles without losing history of the idea.
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
- **Methods:** Oscillator, Price action, Momentum, Multi-factor
- **Tags:** universe:nifty-200, indicator:stochastic, timeframe:intraday-bars, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 1458410
scan_name: "***ShriKrishna RSI3 Consolidation BO"
source_url: https://chartink.com/screener/copy-shrikrishna-rsi3-consolidation-bo-25
market: Indian equities
horizon: Swing
classification: ["Oscillator", "Moving average", "Volume/delivery", "Momentum", "Multi-factor"]
tags: ["universe:nifty-200", "indicator:rsi", "indicator:volume", "indicator:ema", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Oscillator
---

# ***ShriKrishna RSI3 Consolidation BO

## Source

- Chartink URL: https://chartink.com/screener/copy-shrikrishna-rsi3-consolidation-bo-25
- Scan ID: `1458410`
- Slug: `copy-shrikrishna-rsi3-consolidation-bo-25`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2019-11-27T14:13:59.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1458410.json](../source-snapshots/1458410.json)
- Text snapshot: [source-snapshots/1458410.txt](../source-snapshots/1458410.txt)

## What this scan is for

This scan, titled "***ShriKrishna RSI3 Consolidation BO", appears designed to screen Indian equities in the **nifty 200** universe using **5 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Oscillator, Moving average, Volume/delivery, Momentum**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago`.

Author description (source metadata): Star http://www.brokeragesdaytrading.com/article/113259028/how-i-plan-to-use-stockbee-s-breakout-methods/

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: ***ShriKrishna RSI3 Consolidation BO
Scan id: 1458410
Slug: copy-shrikrishna-rsi3-consolidation-bo-25
Source URL: https://chartink.com/screener/copy-shrikrishna-rsi3-consolidation-bo-25
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-27T14:13:59.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] ( daily max( 9 ,  daily high ) - daily min( 9 ,  daily low ) ) / daily close <= .06
2. [Enabled] 1 day ago rsi( 3 ) crossed above 45
3. [Enabled] daily volume > daily ema( volume,9 )
4. [Enabled] daily volume > 51000
5. [Enabled] daily rsi( 3 ) > 63

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( ( latest max( 9 , latest high ) - latest min( 9 , latest low ) ) / latest close <= .06 and 1 day ago rsi( 3 ) > 45 and 2 day ago  rsi( 3 ) <= 45 and latest volume > latest ema( volume,9 ) and latest volume > 51000 and latest rsi( 3 ) > 63 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | ( daily max( 9 ,  daily high ) - daily min( 9 ,  daily low ) ) / daily close <= .06 | Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars. |
| 2 | Enabled | 1 day ago rsi( 3 ) crossed above 45 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period. |
| 3 | Enabled | daily volume > daily ema( volume,9 ) | Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Volume condition gates participation/liquidity. |
| 4 | Enabled | daily volume > 51000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 5 | Enabled | daily rsi( 3 ) > 63 | Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `( daily max( 9 ,  daily high ) - daily min( 9 ,  daily low ) ) / daily close <= .06` — Inequality test: left expression must be less than or equal to right. max(N, series) is the highest value of series over N bars. min(N, series) is the lowest value of series over N bars.
- **#2** `1 day ago rsi( 3 ) crossed above 45` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). RSI is a momentum oscillator from average gains/losses over its period.
- **#3** `daily volume > daily ema( volume,9 )` — Inequality test: left expression must be strictly greater than right. EMA is an exponentially weighted moving average of the chosen field. Volume condition gates participation/liquidity.
- **#4** `daily volume > 51000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#5** `daily rsi( 3 ) > 63` — Inequality test: left expression must be strictly greater than right. RSI is a momentum oscillator from average gains/losses over its period.

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
- `rsi` — appears 2 time(s) in the expression tree
- `volume` — appears 2 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree
- `max` — appears 1 time(s) in the expression tree
- `min` — appears 1 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `ema` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 3 occurrence(s)
- `/` — 1 occurrence(s)
- `<=` — 1 occurrence(s)
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
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Moving average, Volume/delivery, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **5** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Oscillator, Moving average, Volume/delivery, Momentum, Multi-factor
- **Tags:** universe:nifty-200, indicator:rsi, indicator:volume, indicator:ema, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

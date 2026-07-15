---
scan_id: 10761810
scan_name: rsi obv divergence test
source_url: https://chartink.com/screener/rsi-obv-divergence-test
market: Indian equities
horizon: Intraday
classification: ["Volume/delivery", "Oscillator", "Price action", "Multi-factor"]
tags: ["universe:broad-indices", "indicator:rsi", "indicator:volume", "indicator:obv", "timeframe:intraday-bars", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 5
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: broad indices
root_join: all
primary_classification: Volume/delivery
---

# rsi obv divergence test

## Source

- Chartink URL: https://chartink.com/screener/rsi-obv-divergence-test
- Scan ID: `10761810`
- Slug: `rsi-obv-divergence-test`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2023-01-09T13:54:20.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/10761810.json](../source-snapshots/10761810.json)
- Text snapshot: [source-snapshots/10761810.txt](../source-snapshots/10761810.txt)

## What this scan is for

This scan, titled "rsi obv divergence test", appears designed to screen Indian equities in the **broad indices** universe using **5 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Volume/delivery, Oscillator, Price action, Multi-factor**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 5_minute`.

Author description (source metadata): RSI_SOURCE		sma( close * obv , 200 ) / 10000000

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: rsi obv divergence test
Scan id: 10761810
Slug: rsi-obv-divergence-test
Source URL: https://chartink.com/screener/rsi-obv-divergence-test
Root universe/segment: broad indices
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2023-01-09T13:54:20.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] 1 day ago close * 1 day ago volume > 100000000
2. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
3. [Enabled] [3] 5 minute close > [-70] 5 minute close * 1.01
    group_path: root/group[cash|all]
4. [Enabled] [3] 5 minute MY_RSI - [-70] 5 minute MY_RSI < -10
    group_path: root/group[cash|all]
5. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] [-70] 5 minute close > [3] 5 minute close * 1.01
    group_path: root/group[cash|all]
7. [Enabled] [-70] 5 minute MY_RSI - [3] 5 minute MY_RSI < -10
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( broad indices ( 1 day ago close * 1 day ago volume > 100000000 and( cash ( [=-70] 5 minute close > [=3] 5 minute close * 1.01 and [=-70] 5 minute  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" - [=3] 5 minute  "100 - ( 100 /   "1 + (   "ema( greatest(  0,  " ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"" - 1 candle ago  ""(  (   close -   sma(   close , 50 ) ) *  100 /   sma(   close , 50 ) ) -  (  ( rs:'nifty'  close -   sma( rs:'nifty'  close , 50 ) ) *  100 /   sma( rs:'nifty'  close , 50 ) )"""  ) , 14 )" /   "ema(  least(   0,   " "sma(  close *  obv , 200 ) / 10000000" - 1 candle ago  "sma(  close *  obv , 200 ) / 10000000""  ) , 21 ) *  -1" )" )" < -10 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | Disabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Disabled. |
| 3 | Enabled | [3] 5 minute close > [-70] 5 minute close * 1.01 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | Enabled | [3] 5 minute MY_RSI - [-70] 5 minute MY_RSI < -10 | Inequality test: left expression must be strictly less than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 6 | Enabled | [-70] 5 minute close > [3] 5 minute close * 1.01 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 7 | Enabled | [-70] 5 minute MY_RSI - [3] 5 minute MY_RSI < -10 | Inequality test: left expression must be strictly less than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **5** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#3** `[3] 5 minute close > [-70] 5 minute close * 1.01` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#4** `[3] 5 minute MY_RSI - [-70] 5 minute MY_RSI < -10` — Inequality test: left expression must be strictly less than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[-70] 5 minute close > [3] 5 minute close * 1.01` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `[-70] 5 minute MY_RSI - [3] 5 minute MY_RSI < -10` — Inequality test: left expression must be strictly less than right. RSI is a momentum oscillator from average gains/losses over its period. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `close` — appears 5 time(s) in the expression tree
- `custom_indicator_13107` — appears 4 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `*` — 3 occurrence(s)
- `>` — 3 occurrence(s)
- `-` — 2 occurrence(s)
- `<` — 2 occurrence(s)

### General calculation semantics used in this corpus
- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.
- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.
- **max(N, series) / min(N, series)** are rolling extrema.
- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.
- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.
- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.
- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.

### Scan-level settings (from root group)
- Universe/segment: **broad indices**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `5_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **broad indices**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Oscillator, Price action, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **5** active filters — transparent screening logic.
- Universe pinned to **broad indices**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- Participation filters help de-emphasise thin prints that only move on tiny size.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Volume/delivery, Oscillator, Price action, Multi-factor
- **Tags:** universe:broad-indices, indicator:rsi, indicator:volume, indicator:obv, timeframe:intraday-bars, timeframe:daily
- **Root universe:** broad indices
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

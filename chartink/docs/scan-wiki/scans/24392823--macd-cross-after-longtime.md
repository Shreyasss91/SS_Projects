---
scan_id: 24392823
scan_name: macd cross after longtime
source_url: https://chartink.com/screener/macd-cross-after-longtime
market: Indian equities
horizon: Swing
classification: ["Oscillator", "Fundamental", "Momentum", "Multi-factor"]
tags: ["long-bias", "universe:cash", "indicator:macd", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 4
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Oscillator
---

# macd cross after longtime

## Source

- Chartink URL: https://chartink.com/screener/macd-cross-after-longtime
- Scan ID: `24392823`
- Slug: `macd-cross-after-longtime`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2025-11-06T01:39:04.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/24392823.json](../source-snapshots/24392823.json)
- Text snapshot: [source-snapshots/24392823.txt](../source-snapshots/24392823.txt)

## What this scan is for

This scan, titled "macd cross after longtime", appears designed to screen Indian equities in the **cash** universe using **4 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Oscillator, Fundamental, Momentum, Multi-factor**. Likely horizon label from name/timeframes: **Swing**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 0_quarters_ago, 1_days_ago, 1_quarters_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: macd cross after longtime
Scan id: 24392823
Slug: macd-cross-after-longtime
Source URL: https://chartink.com/screener/macd-cross-after-longtime
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2025-11-06T01:39:04.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] daily market cap > 3000
    group_path: root/group[cash|all]
3. [Enabled] 0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage
    group_path: root/group[cash|all]
4. [Enabled] daily macd line( 26 ,  12 ,  9 ) crossed above daily macd signal( 26 ,  12 ,  9 )
5. [Enabled] 1 day ago count( 30, 1 where daily macd line( 26 ,  12 ,  9 ) < daily macd signal( 26 ,  12 ,  9 ) ) = 30

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( cash ( ( cash ( market cap > 3000 and quarterly foreign institutional investors percentage > 1 quarter ago foreign institutional investors percentage ) ) and daily macd line( 26 , 12 , 9 ) > daily macd signal( 26 , 12 , 9 ) and 1 day ago  macd line( 26 , 12 , 9 ) <= 1 day ago  macd signal( 26 , 12 , 9 ) and 1 day ago count( 30, 1 where daily macd line( 26 , 12 , 9 ) < daily macd signal( 26 , 12 , 9 ) ) = 30 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 2 | Enabled | daily market cap > 3000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 3 | Enabled | 0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage | Inequality test: left expression must be strictly greater than right. |
| 4 | Enabled | daily macd line( 26 ,  12 ,  9 ) crossed above daily macd signal( 26 ,  12 ,  9 ) | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). MACD uses EMA differences (line/signal/histogram depending on field). |
| 5 | Enabled | 1 day ago count( 30, 1 where daily macd line( 26 ,  12 ,  9 ) < daily macd signal( 26 ,  12 ,  9 ) ) = 30 | Inequality test: left expression must be strictly less than right. MACD uses EMA differences (line/signal/histogram depending on field). |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **4** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `daily market cap > 3000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#3** `0 quarters ago foreign institutional investors percentage > 1 quarters ago foreign institutional investors percentage` — Inequality test: left expression must be strictly greater than right.
- **#4** `daily macd line( 26 ,  12 ,  9 ) crossed above daily macd signal( 26 ,  12 ,  9 )` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). MACD uses EMA differences (line/signal/histogram depending on field).
- **#5** `1 day ago count( 30, 1 where daily macd line( 26 ,  12 ,  9 ) < daily macd signal( 26 ,  12 ,  9 ) ) = 30` — Inequality test: left expression must be strictly less than right. MACD uses EMA differences (line/signal/histogram depending on field).

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
- `foreign institutional investors percentage` — appears 2 time(s) in the expression tree
- `macd line` — appears 2 time(s) in the expression tree
- `macd signal` — appears 2 time(s) in the expression tree
- `market cap` — appears 1 time(s) in the expression tree
- `count` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 2 occurrence(s)
- `crossed above` — 1 occurrence(s)
- `=` — 1 occurrence(s)
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
- Universe/segment: **cash**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `0_quarters_ago`, `1_days_ago`, `1_quarters_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Oscillator, Fundamental, Momentum, Multi-factor.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **4** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Oscillator, Fundamental, Momentum, Multi-factor
- **Tags:** long-bias, universe:cash, indicator:macd, timeframe:daily
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

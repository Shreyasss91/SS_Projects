---
scan_id: 25173278
scan_name: INTRADAY STOCK
source_url: https://chartink.com/screener/intraday-stock-9123511
market: Indian equities
horizon: Intraday
classification: ["Moving average", "Volume/delivery"]
tags: ["universe:nifty-200", "indicator:volume", "indicator:sma", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Moving average
---

# INTRADAY STOCK

## Source

- Chartink URL: https://chartink.com/screener/intraday-stock-9123511
- Scan ID: `25173278`
- Slug: `intraday-stock-9123511`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2026-01-25T14:15:44.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/25173278.json](../source-snapshots/25173278.json)
- Text snapshot: [source-snapshots/25173278.txt](../source-snapshots/25173278.txt)

## What this scan is for

This scan, titled "INTRADAY STOCK", appears designed to screen Indian equities in the **nifty 200** universe using **6 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Moving average, Volume/delivery**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: INTRADAY STOCK
Scan id: 25173278
Slug: intraday-stock-9123511
Source URL: https://chartink.com/screener/intraday-stock-9123511
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2026-01-25T14:15:44.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=any_2 combination=passes measurevalue=default]  (path: root/group[cash|any_2])
2. [Enabled] 1 day ago volume > 1 day ago sma( close ,  20 ) * 2
    group_path: root/group[cash|any_2]
3. [Enabled] daily open > 1 day ago close * 1.010
    group_path: root/group[cash|any_2]
4. [Enabled] daily open < 1 day ago close * 0.99
    group_path: root/group[cash|any_2]
5. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] 1 day ago volume > 1 day ago sma( close ,  20 ) * 2
    group_path: root/group[cash|all]
7. [Enabled] daily open < 1 day ago close * 1.010
    group_path: root/group[cash|all]
8. [Enabled] daily open > 1 day ago close * 0.99
    group_path: root/group[cash|all]

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( ( cash (  1 day ago volume >  1 day ago sma(  daily volume , 20 ) *  2 and  daily open <  1 day ago close *  1.010 and  daily open >  1 day ago close *  0.99 ) ) ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Disabled | [GROUP segment=cash join=any_2 combination=passes measurevalue=default] | Nested group over segment **cash** with join **any_2** (combination=passes). Group status=Disabled. |
| 2 | Enabled | 1 day ago volume > 1 day ago sma( close ,  20 ) * 2 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 3 | Enabled | daily open > 1 day ago close * 1.010 | Inequality test: left expression must be strictly greater than right. |
| 4 | Enabled | daily open < 1 day ago close * 0.99 | Inequality test: left expression must be strictly less than right. |
| 5 | Enabled | [GROUP segment=cash join=all combination=passes measurevalue=default] | Nested group over segment **cash** with join **all** (combination=passes). Group status=Enabled. |
| 6 | Enabled | 1 day ago volume > 1 day ago sma( close ,  20 ) * 2 | Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity. |
| 7 | Enabled | daily open < 1 day ago close * 1.010 | Inequality test: left expression must be strictly less than right. |
| 8 | Enabled | daily open > 1 day ago close * 0.99 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago volume > 1 day ago sma( close ,  20 ) * 2` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#3** `daily open > 1 day ago close * 1.010` — Inequality test: left expression must be strictly greater than right.
- **#4** `daily open < 1 day ago close * 0.99` — Inequality test: left expression must be strictly less than right.
- **#6** `1 day ago volume > 1 day ago sma( close ,  20 ) * 2` — Inequality test: left expression must be strictly greater than right. SMA is the arithmetic mean of the chosen field over N bars. Volume condition gates participation/liquidity.
- **#7** `daily open < 1 day ago close * 1.010` — Inequality test: left expression must be strictly less than right.
- **#8** `daily open > 1 day ago close * 0.99` — Inequality test: left expression must be strictly greater than right.

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
- `volume` — appears 4 time(s) in the expression tree
- `open` — appears 4 time(s) in the expression tree
- `close` — appears 4 time(s) in the expression tree
- `sma` — appears 2 time(s) in the expression tree

### Operators observed
- `*` — 6 occurrence(s)
- `>` — 4 occurrence(s)
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
- Universe/segment: **nifty 200**
- Join: **all**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Moving average, Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Moving average, Volume/delivery
- **Tags:** universe:nifty-200, indicator:volume, indicator:sma, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 1433762
scan_name: EOD Jackpot -- COMPRESSING CANDLES -- ORIGINAL
source_url: https://chartink.com/screener/copy-eod-jackpot-49
market: Indian equities
horizon: Intraday
classification: ["Price action"]
tags: ["universe:nifty-200", "timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 17
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: nifty 200
root_join: all
primary_classification: Price action
---

# EOD Jackpot -- COMPRESSING CANDLES -- ORIGINAL

## Source

- Chartink URL: https://chartink.com/screener/copy-eod-jackpot-49
- Scan ID: `1433762`
- Slug: `copy-eod-jackpot-49`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2019-11-19T11:27:52.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/1433762.json](../source-snapshots/1433762.json)
- Text snapshot: [source-snapshots/1433762.txt](../source-snapshots/1433762.txt)

## What this scan is for

This scan, titled "EOD Jackpot -- COMPRESSING CANDLES -- ORIGINAL", appears designed to screen Indian equities in the **nifty 200** universe using **17 enabled** condition(s) combined with root join **all (AND)**.

Dominant method tag(s) inferred from conditions: **Price action**. Likely horizon label from name/timeframes: **Intraday**.

Observed Chartink timeframe offsets in the tree: `0_days_ago, 1_days_ago, 2_days_ago, 3_days_ago, 4_days_ago`.

This is an educational reconstruction of screening intent from the captured definition; it is not a performance claim or trade recommendation.

## Exact Chartink scan definition

```text
Scan name: EOD Jackpot -- COMPRESSING CANDLES -- ORIGINAL
Scan id: 1433762
Slug: copy-eod-jackpot-49
Source URL: https://chartink.com/screener/copy-eod-jackpot-49
Root universe/segment: nifty 200
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2019-11-19T11:27:52.000000Z

=== Condition tree (from atlas_json; includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=nifty 200 join=any combination=passes measurevalue=default]  (path: root/group[nifty 200|any])
2. [Enabled] [GROUP segment=nifty 200 join=all combination=passes measurevalue=default]  (path: root/group[nifty 200|any]/group[nifty 200|all])
3. [Enabled] 2 days ago high > 1 day ago high
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
4. [Enabled] 2 days ago low < 1 day ago low
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
5. [Enabled] 1 day ago high > daily high
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
6. [Enabled] 1 day ago low < daily low
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
7. [Enabled] [GROUP segment=nifty 200 join=all combination=passes measurevalue=default]  (path: root/group[nifty 200|any]/group[nifty 200|all])
8. [Enabled] 4 days ago high > 3 days ago high
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
9. [Enabled] 4 days ago low > 3 days ago low
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
10. [Enabled] 4 days ago high > 2 days ago high
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
11. [Enabled] 3 days ago low < 2 days ago low
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
12. [Enabled] 2 days ago high > 1 day ago high
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
13. [Enabled] 2 days ago low < 1 day ago low
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
14. [Enabled] [GROUP segment=nifty 200 join=all combination=passes measurevalue=default]  (path: root/group[nifty 200|any]/group[nifty 200|all])
15. [Enabled] 4 days ago high < 3 days ago high
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
16. [Enabled] 4 days ago low < 3 days ago low
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
17. [Enabled] 3 days ago high > 2 days ago high
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
18. [Enabled] 4 days ago low < 2 days ago low
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
19. [Enabled] 2 days ago high > 1 day ago high
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
20. [Enabled] 2 days ago low < 1 day ago low
    group_path: root/group[nifty 200|any]/group[nifty 200|all]
21. [Enabled] daily close > 50

=== Chartink atlas_query (compiled/active form; typically omits disabled filters) ===

( nifty 200 ( ( nifty 200 ( ( nifty 200 ( 2 days ago high > 1 day ago high and 2 days ago low < 1 day ago low and 1 day ago high > latest high and 1 day ago low < latest low ) ) or( nifty 200 ( 4 days ago high > 3 days ago high and 4 days ago low > 3 days ago low and 4 days ago high > 2 days ago high and 3 days ago low < 2 days ago low and 2 days ago high > 1 day ago high and 2 days ago low < 1 day ago low ) ) or( nifty 200 ( 4 days ago high < 3 days ago high and 4 days ago low < 3 days ago low and 3 days ago high > 2 days ago high and 4 days ago low < 2 days ago low and 2 days ago high > 1 day ago high and 2 days ago low < 1 day ago low ) ) ) ) and latest close > 50 ) )
```

## Filter status and interpretation

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | [GROUP segment=nifty 200 join=any combination=passes measurevalue=default] | Nested group over segment **nifty 200** with join **any** (combination=passes). Group status=Enabled. |
| 2 | Enabled | [GROUP segment=nifty 200 join=all combination=passes measurevalue=default] | Nested group over segment **nifty 200** with join **all** (combination=passes). Group status=Enabled. |
| 3 | Enabled | 2 days ago high > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 4 | Enabled | 2 days ago low < 1 day ago low | Inequality test: left expression must be strictly less than right. |
| 5 | Enabled | 1 day ago high > daily high | Inequality test: left expression must be strictly greater than right. |
| 6 | Enabled | 1 day ago low < daily low | Inequality test: left expression must be strictly less than right. |
| 7 | Enabled | [GROUP segment=nifty 200 join=all combination=passes measurevalue=default] | Nested group over segment **nifty 200** with join **all** (combination=passes). Group status=Enabled. |
| 8 | Enabled | 4 days ago high > 3 days ago high | Inequality test: left expression must be strictly greater than right. |
| 9 | Enabled | 4 days ago low > 3 days ago low | Inequality test: left expression must be strictly greater than right. |
| 10 | Enabled | 4 days ago high > 2 days ago high | Inequality test: left expression must be strictly greater than right. |
| 11 | Enabled | 3 days ago low < 2 days ago low | Inequality test: left expression must be strictly less than right. |
| 12 | Enabled | 2 days ago high > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 13 | Enabled | 2 days ago low < 1 day ago low | Inequality test: left expression must be strictly less than right. |
| 14 | Enabled | [GROUP segment=nifty 200 join=all combination=passes measurevalue=default] | Nested group over segment **nifty 200** with join **all** (combination=passes). Group status=Enabled. |
| 15 | Enabled | 4 days ago high < 3 days ago high | Inequality test: left expression must be strictly less than right. |
| 16 | Enabled | 4 days ago low < 3 days ago low | Inequality test: left expression must be strictly less than right. |
| 17 | Enabled | 3 days ago high > 2 days ago high | Inequality test: left expression must be strictly greater than right. |
| 18 | Enabled | 4 days ago low < 2 days ago low | Inequality test: left expression must be strictly less than right. |
| 19 | Enabled | 2 days ago high > 1 day ago high | Inequality test: left expression must be strictly greater than right. |
| 20 | Enabled | 2 days ago low < 1 day ago low | Inequality test: left expression must be strictly less than right. |
| 21 | Enabled | daily close > 50 | Inequality test: left expression must be strictly greater than right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups may introduce additional AND/OR scopes (see group rows and `group_path` in the filter table).
There are **17** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#3** `2 days ago high > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#4** `2 days ago low < 1 day ago low` — Inequality test: left expression must be strictly less than right.
- **#5** `1 day ago high > daily high` — Inequality test: left expression must be strictly greater than right.
- **#6** `1 day ago low < daily low` — Inequality test: left expression must be strictly less than right.
- **#8** `4 days ago high > 3 days ago high` — Inequality test: left expression must be strictly greater than right.
- **#9** `4 days ago low > 3 days ago low` — Inequality test: left expression must be strictly greater than right.
- **#10** `4 days ago high > 2 days ago high` — Inequality test: left expression must be strictly greater than right.
- **#11** `3 days ago low < 2 days ago low` — Inequality test: left expression must be strictly less than right.
- **#12** `2 days ago high > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#13** `2 days ago low < 1 day ago low` — Inequality test: left expression must be strictly less than right.
- **#15** `4 days ago high < 3 days ago high` — Inequality test: left expression must be strictly less than right.
- **#16** `4 days ago low < 3 days ago low` — Inequality test: left expression must be strictly less than right.
- **#17** `3 days ago high > 2 days ago high` — Inequality test: left expression must be strictly greater than right.
- **#18** `4 days ago low < 2 days ago low` — Inequality test: left expression must be strictly less than right.
- **#19** `2 days ago high > 1 day ago high` — Inequality test: left expression must be strictly greater than right.
- **#20** `2 days ago low < 1 day ago low` — Inequality test: left expression must be strictly less than right.
- **#21** `daily close > 50` — Inequality test: left expression must be strictly greater than right.

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
- `high` — appears 16 time(s) in the expression tree
- `low` — appears 16 time(s) in the expression tree
- `close` — appears 1 time(s) in the expression tree

### Operators observed
- `>` — 9 occurrence(s)
- `<` — 8 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`, `2_days_ago`, `3_days_ago`, `4_days_ago`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **nifty 200**. Liquidity and index membership still vary inside that set.
- **Method context:** Price action.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **17** active filters — transparent screening logic.
- Universe pinned to **nifty 200**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Price action
- **Tags:** universe:nifty-200, timeframe:daily
- **Root universe:** nifty 200
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 7397158
scan_name: Shakeout of small cap stocks intraday
source_url: https://chartink.com/screener/shakeout-of-small-cap-stocks-intraday
market: Indian equities
horizon: Intraday
classification: ["Fundamental"]
tags: ["bias:upward-condition", "bias:downward-condition", "universe:cash", "timeframe:daily", "timeframe:intraday-bars"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: any
primary_classification: Fundamental
---

# Shakeout of small cap stocks intraday

## Source

- Chartink URL: https://chartink.com/screener/shakeout-of-small-cap-stocks-intraday
- Scan ID: `7397158`
- Slug: `shakeout-of-small-cap-stocks-intraday`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Intraday
- Created at (Chartink): 2022-01-06T04:16:42.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/7397158.json](../source-snapshots/7397158.json)
- Text snapshot: [source-snapshots/7397158.txt](../source-snapshots/7397158.txt)

## What this scan is for

This is a **intraday** screen over **cash** with **6** active leaf condition(s) under root join **any (OR)**.
Its method labels are derived only from active expressions: **Fundamental**.
The active tests, in captured order, are:
- [0] 60 minute low < daily least * 0.98
- daily market cap > 1000
- daily market cap < 10000
- [0] 60 minute high > daily greatest * 01.02
- daily market cap > 1000
- daily market cap < 10000

Author description (source metadata): MCAP between 1000 to 10000 crores

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Shakeout of small cap stocks intraday
Scan id: 7397158
Slug: shakeout-of-small-cap-stocks-intraday
Source URL: https://chartink.com/screener/shakeout-of-small-cap-stocks-intraday
Root universe/segment: cash
Root join: any (OR)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-01-06T04:16:42.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] [0] 60 minute low < daily least * 0.98
    group_path: root/group[cash|all]
3. [Enabled] daily market cap > 1000
    group_path: root/group[cash|all]
4. [Enabled] daily market cap < 10000
    group_path: root/group[cash|all]
5. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
6. [Enabled] [0] 60 minute high > daily greatest * 01.02
    group_path: root/group[cash|all]
7. [Enabled] daily market cap > 1000
    group_path: root/group[cash|all]
8. [Enabled] daily market cap < 10000
    group_path: root/group[cash|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( [0] 1 hour low < least(  [0] 1 hour open, [0] 1 hour close  ) * 0.98 and market cap > 1000 and market cap < 10000 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | [0] 60 minute low < daily least * 0.98 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 2 | 3 | Enabled | root/group[cash\|all] | daily market cap > 1000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 3 | 4 | Enabled | root/group[cash\|all] | daily market cap < 10000 | Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 4 | 6 | Enabled | root/group[cash\|all] | [0] 60 minute high > daily greatest * 01.02 | Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 7 | Enabled | root/group[cash\|all] | daily market cap > 1000 | Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals. |
| 6 | 8 | Enabled | root/group[cash\|all] | daily market cap < 10000 | Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals. |

## How the enabled logic works

Root group join is **OR (any may pass)**. Nested groups may introduce additional AND/OR scopes (see the rendered source tree and the group-scope column in the filter table).
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `[0] 60 minute low < daily least * 0.98` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#3** `daily market cap > 1000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#4** `daily market cap < 10000` — Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#6** `[0] 60 minute high > daily greatest * 01.02` — Inequality test: left expression must be strictly greater than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#7** `daily market cap > 1000` — Inequality test: left expression must be strictly greater than right. Filters by market-capitalisation field from Chartink fundamentals.
- **#8** `daily market cap < 10000` — Inequality test: left expression must be strictly less than right. Filters by market-capitalisation field from Chartink fundamentals.

Combined effect:
- With root join **any**, the scan is broader (union of conditions).
- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).
- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.
- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.

## Disabled filters

No disabled leaf conditions were present in the captured `atlas_json` tree. Nothing additional is withheld solely by UI disable toggles at the condition level.

## Calculation notes

Notes below are tied to measures actually present in this scan's tree. Chartink-specific aggregation/session rules are used as Chartink implements them; where the export does not document a quirk, uncertainty is left explicit.

### Measures observed
- `market cap` — appears 4 time(s) in the expression tree
- `open` — appears 2 time(s) in the expression tree
- `close` — appears 2 time(s) in the expression tree
- `low` — appears 1 time(s) in the expression tree
- `least` — appears 1 time(s) in the expression tree
- `high` — appears 1 time(s) in the expression tree
- `greatest` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 3 occurrence(s)
- `>` — 3 occurrence(s)
- `*` — 2 occurrence(s)

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
- Join: **any**
- Combination: **passes**
- Measurevalue: **default**
- Timeframe tokens: `0_days_ago`, `60_minute`

## How to use it

- **Horizon context:** treat as **Intraday** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Fundamental.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- OR-combined root group can cast a wider net across related patterns.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- OR logic can admit symbols that only match a weak branch of the idea.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Intraday
- **Methods:** Fundamental
- **Tags:** bias:upward-condition, bias:downward-condition, universe:cash, timeframe:daily, timeframe:intraday-bars
- **Root universe:** cash
- **Root join:** any
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

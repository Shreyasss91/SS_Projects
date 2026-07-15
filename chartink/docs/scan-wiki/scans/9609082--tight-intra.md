---
scan_id: 9609082
scan_name: tight intra
source_url: https://chartink.com/screener/tight-intra
market: Indian equities
horizon: "Multi-horizon"
classification: ["Volume/delivery","Momentum"]
tags: ["universe:cash","indicator:volume","timeframe:daily","timeframe:intraday-bars","timeframe:monthly"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 6
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: cash
root_join: all
primary_classification: Volume/delivery
---

# tight intra

## Source

- Chartink URL: https://chartink.com/screener/tight-intra
- Scan ID: `9609082`
- Slug: `tight-intra`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Multi-horizon
- Created at (Chartink): 2022-09-10T18:03:55.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/9609082.json](../source-snapshots/9609082.json)
- Text snapshot: [source-snapshots/9609082.txt](../source-snapshots/9609082.txt)

## What this scan is for

This is a **multi-horizon** screen over **cash** with **6** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery, Momentum**.

The active tests, in captured order:
- 1 day ago close * 1 day ago volume > 100000000
- [0] 5 minute count( 75, 1 where daily abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.03 ) crossed above 40
- [0] 5 minute count( 70, 1 where [0] 5 minute high / [0] 5 minute low = 1 ) < 5
- [0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20
- [0] 5 minute count( 75, 1 where daily abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.04 ) crossed above 40
- [0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: tight intra
Scan id: 9609082
Slug: tight-intra
Source URL: https://chartink.com/screener/tight-intra
Root universe/segment: cash
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2022-09-10T18:03:55.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Disabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
2. [Enabled] 1 day ago close * 1 day ago volume > 100000000
    group_path: root/group[cash|all]
3. [Enabled] [GROUP segment=cash join=all combination=passes measurevalue=default]  (path: root/group[cash|all])
4. [Enabled] [0] 5 minute count( 75, 1 where daily abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.03 ) crossed above 40
    group_path: root/group[cash|all]
5. [Enabled] [0] 5 minute count( 70, 1 where [0] 5 minute high / [0] 5 minute low = 1 ) < 5
    group_path: root/group[cash|all]
6. [Enabled] [0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20
    group_path: root/group[cash|all]
7. [Disabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|all])
8. [Enabled] [0] 5 minute count( 75, 1 where daily abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.04 ) crossed above 40
    group_path: root/group[futures|all]
9. [Enabled] [0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20
    group_path: root/group[futures|all]

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( cash ( ( cash ( [0] 5 minute count( 75, 1 where abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.03 ) > 40 and [ -1 ] 5 minute count( 75, 1 where abs( ( [0] 5 minute close / [ -2 ] 5 minute close * 100 ) - 100 ) < 0.03 ) <= 40 and [0] 5 minute count( 70, 1 where [0] 5 minute high / [0] 5 minute low = 1 ) < 5 and [0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20 ) ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 2 | Enabled | root/group[cash\|all] | 1 day ago close * 1 day ago volume > 100000000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 2 | 4 | Enabled | root/group[cash\|all] | [0] 5 minute count( 75, 1 where daily abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.03 ) crossed above 40 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 3 | 5 | Enabled | root/group[cash\|all] | [0] 5 minute count( 70, 1 where [0] 5 minute high / [0] 5 minute low = 1 ) < 5 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 4 | 6 | Enabled | root/group[cash\|all] | [0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 5 | 8 | Enabled | root/group[futures\|all] | [0] 5 minute count( 75, 1 where daily abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.04 ) crossed above 40 | Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data. |
| 6 | 9 | Enabled | root/group[futures\|all] | [0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20 | Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **6** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#2** `1 day ago close * 1 day ago volume > 100000000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#4** `[0] 5 minute count( 75, 1 where daily abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.03 ) crossed above 40` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#5** `[0] 5 minute count( 70, 1 where [0] 5 minute high / [0] 5 minute low = 1 ) < 5` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#6** `[0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#8** `[0] 5 minute count( 75, 1 where daily abs( ( [0] 5 minute close / [-1] 5 minute close * 100 ) - 100 ) < 0.04 ) crossed above 40` — Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar). Uses an intraday bar size (minute timeframe) rather than daily-only data.
- **#9** `[0] 5 minute count( 70, 1 where [0] 5 minute high - [0] 5 minute low = 0.05 ) < 20` — Inequality test: left expression must be strictly less than right. Uses an intraday bar size (minute timeframe) rather than daily-only data.

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
- `count` — appears 5 time(s) in the expression tree
- `high` — appears 3 time(s) in the expression tree
- `low` — appears 3 time(s) in the expression tree
- `abs` — appears 2 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `<` — 5 occurrence(s)
- `=` — 3 occurrence(s)
- `crossed above` — 2 occurrence(s)
- `-` — 2 occurrence(s)
- `*` — 1 occurrence(s)
- `>` — 1 occurrence(s)
- `/` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `0_months_ago`, `1_days_ago`, `5_minute`

## How to use it

- **Horizon context:** treat as **Multi-horizon** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **cash**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery, Momentum.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **6** active filters — transparent screening logic.
- Universe pinned to **cash**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Multi-horizon
- **Methods:** Volume/delivery, Momentum
- **Tags:** universe:cash, indicator:volume, timeframe:daily, timeframe:intraday-bars, timeframe:monthly
- **Root universe:** cash
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

---
scan_id: 2568305
scan_name: Copy - Golden Bounce Master 3.5
source_url: https://chartink.com/screener/copy-golden-bounce-master-3-5-13
market: Indian equities
horizon: "Swing"
classification: ["Volume/delivery"]
tags: ["universe:futures","indicator:volume","timeframe:daily"]
captured_at: "2026-07-15T12:56:06+05:30"
enabled_filter_count: 20
disabled_filter_count: 0
needs_review_filter_count: 0
root_segment: futures
root_join: all
primary_classification: Volume/delivery
---

# Copy - Golden Bounce Master 3.5

## Source

- Chartink URL: https://chartink.com/screener/copy-golden-bounce-master-3-5-13
- Scan ID: `2568305`
- Slug: `copy-golden-bounce-master-3-5-13`
- Captured: 2026-07-15T12:56:06+05:30
- Market: Indian equities
- Intended horizon: Swing
- Created at (Chartink): 2020-07-23T02:57:56.000000Z
- Private: False
- Favourite flag: 0
- Alert present flag: 0
- Raw snapshot: [source-snapshots/2568305.json](../source-snapshots/2568305.json)
- Text snapshot: [source-snapshots/2568305.txt](../source-snapshots/2568305.txt)

## What this scan is for

This is a **swing** screen over **futures** with **20** active leaf condition(s) under root join **all**.
Its method labels are derived only from active expressions: **Volume/delivery**.

The active tests, in captured order:
- daily close > 100
- daily close < 5000
- daily volume > 100000
- ( ( daily high - ( ( daily high - daily low ) * 0.618 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 )
- ( ( daily high - ( ( daily high - daily low ) * 0.618 ) ) - ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) <= ( daily high * 0.001 )
- daily high >= ( 1 day ago close * 1.015 )
- ( daily high - daily open ) > ( daily open - daily low )
- ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( daily high - ( ( daily high - daily low ) * 0.618 ) )
- ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( daily high - ( ( daily high - daily low ) * 0.618 ) ) ) <= ( daily high * 0.001 )
- daily high >= ( 1 day ago close * 1.015 )
- ( daily high - daily open ) > ( daily open - daily low )
- ( ( daily high - ( ( daily high - daily low ) * 0.382 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 )
- ( ( daily high - ( ( daily high - daily low ) * 0.382 ) ) - ( ( 1 day ago high + 1 day ago low + daily close ) / 3 ) ) <= ( daily high * 0.001 )
- daily low <= ( 1 day ago close * 0.985 )
- ( daily high - daily open ) < ( daily open - daily low )
- ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( daily high - ( ( daily high - daily low ) * 0.382 ) )
- ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( daily high - ( ( daily high - daily low ) * 0.382 ) ) ) <= ( daily high * 0.001 )
- daily low <= ( 1 day ago close * 0.985 )
- ( daily high - daily open ) < ( daily open - daily low )
- ( daily high - ( ( daily high - daily low ) * 0.382 ) ) - ( daily high - ( ( daily high - daily low ) * 0.618 ) ) >= ( daily high * 0.006 )

This explains the captured screen mechanically; it is not a performance claim or trade recommendation.

## Source-faithful rendered filter tree

```text
Scan name: Copy - Golden Bounce Master 3.5
Scan id: 2568305
Slug: copy-golden-bounce-master-3-5-13
Source URL: https://chartink.com/screener/copy-golden-bounce-master-3-5-13
Root universe/segment: futures
Root join: all (AND)
Root combination: passes
Root measurevalue: default
is_private: False
created_at: 2020-07-23T02:57:56.000000Z

=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===

1. [Enabled] daily close > 100
2. [Enabled] daily close < 5000
3. [Enabled] daily volume > 100000
4. [Enabled] [GROUP segment=futures join=any combination=passes measurevalue=default]  (path: root/group[futures|any])
5. [Enabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|any]/group[futures|all])
6. [Enabled] ( ( daily high - ( ( daily high - daily low ) * 0.618 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 )
    group_path: root/group[futures|any]/group[futures|all]
7. [Enabled] ( ( daily high - ( ( daily high - daily low ) * 0.618 ) ) - ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) <= ( daily high * 0.001 )
    group_path: root/group[futures|any]/group[futures|all]
8. [Enabled] daily high >= ( 1 day ago close * 1.015 )
    group_path: root/group[futures|any]/group[futures|all]
9. [Enabled] ( daily high - daily open ) > ( daily open - daily low )
    group_path: root/group[futures|any]/group[futures|all]
10. [Enabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|any]/group[futures|all])
11. [Enabled] ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( daily high - ( ( daily high - daily low ) * 0.618 ) )
    group_path: root/group[futures|any]/group[futures|all]
12. [Enabled] ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( daily high - ( ( daily high - daily low ) * 0.618 ) ) ) <= ( daily high * 0.001 )
    group_path: root/group[futures|any]/group[futures|all]
13. [Enabled] daily high >= ( 1 day ago close * 1.015 )
    group_path: root/group[futures|any]/group[futures|all]
14. [Enabled] ( daily high - daily open ) > ( daily open - daily low )
    group_path: root/group[futures|any]/group[futures|all]
15. [Enabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|any]/group[futures|all])
16. [Enabled] ( ( daily high - ( ( daily high - daily low ) * 0.382 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 )
    group_path: root/group[futures|any]/group[futures|all]
17. [Enabled] ( ( daily high - ( ( daily high - daily low ) * 0.382 ) ) - ( ( 1 day ago high + 1 day ago low + daily close ) / 3 ) ) <= ( daily high * 0.001 )
    group_path: root/group[futures|any]/group[futures|all]
18. [Enabled] daily low <= ( 1 day ago close * 0.985 )
    group_path: root/group[futures|any]/group[futures|all]
19. [Enabled] ( daily high - daily open ) < ( daily open - daily low )
    group_path: root/group[futures|any]/group[futures|all]
20. [Enabled] [GROUP segment=futures join=all combination=passes measurevalue=default]  (path: root/group[futures|any]/group[futures|all])
21. [Enabled] ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( daily high - ( ( daily high - daily low ) * 0.382 ) )
    group_path: root/group[futures|any]/group[futures|all]
22. [Enabled] ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( daily high - ( ( daily high - daily low ) * 0.382 ) ) ) <= ( daily high * 0.001 )
    group_path: root/group[futures|any]/group[futures|all]
23. [Enabled] daily low <= ( 1 day ago close * 0.985 )
    group_path: root/group[futures|any]/group[futures|all]
24. [Enabled] ( daily high - daily open ) < ( daily open - daily low )
    group_path: root/group[futures|any]/group[futures|all]
25. [Enabled] ( daily high - ( ( daily high - daily low ) * 0.382 ) ) - ( daily high - ( ( daily high - daily low ) * 0.618 ) ) >= ( daily high * 0.006 )

=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===

( futures ( latest close > 100 and latest close < 5000 and latest volume > 100000 and( futures ( ( futures ( ( ( latest high - ( ( latest high - latest low ) * 0.618 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) and( ( latest high - ( ( latest high - latest low ) * 0.618 ) ) - ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) <= ( latest high * 0.001 ) and latest high >= ( 1 day ago close * 1.015 ) and( latest high - latest open ) > ( latest open - latest low ) ) ) or( futures ( ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( latest high - ( ( latest high - latest low ) * 0.618 ) ) and( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( latest high - ( ( latest high - latest low ) * 0.618 ) ) ) <= ( latest high * 0.001 ) and latest high >= ( 1 day ago close * 1.015 ) and( latest high - latest open ) > ( latest open - latest low ) ) ) or( futures ( ( ( latest high - ( ( latest high - latest low ) * 0.382 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) and( ( latest high - ( ( latest high - latest low ) * 0.382 ) ) - ( ( 1 day ago high + 1 day ago low + latest close ) / 3 ) ) <= ( latest high * 0.001 ) and latest low <= ( 1 day ago close * 0.985 ) and( latest high - latest open ) < ( latest open - latest low ) ) ) or( futures ( ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( latest high - ( ( latest high - latest low ) * 0.382 ) ) and( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( latest high - ( ( latest high - latest low ) * 0.382 ) ) ) <= ( latest high * 0.001 ) and latest low <= ( 1 day ago close * 0.985 ) and( latest high - latest open ) < ( latest open - latest low ) ) ) ) ) and( latest high - ( ( latest high - latest low ) * 0.382 ) ) - ( latest high - ( ( latest high - latest low ) * 0.618 ) ) >= ( latest high * 0.006 ) ) )
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
| 1 | 1 | Enabled | root | daily close > 100 | Inequality test: left expression must be strictly greater than right. |
| 2 | 2 | Enabled | root | daily close < 5000 | Inequality test: left expression must be strictly less than right. |
| 3 | 3 | Enabled | root | daily volume > 100000 | Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity. |
| 4 | 6 | Enabled | root/group[futures\|any]/group[futures\|all] | ( ( daily high - ( ( daily high - daily low ) * 0.618 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) | Inequality test: left expression must be greater than or equal to right. |
| 5 | 7 | Enabled | root/group[futures\|any]/group[futures\|all] | ( ( daily high - ( ( daily high - daily low ) * 0.618 ) ) - ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) <= ( daily high * 0.001 ) | Inequality test: left expression must be less than or equal to right. |
| 6 | 8 | Enabled | root/group[futures\|any]/group[futures\|all] | daily high >= ( 1 day ago close * 1.015 ) | Inequality test: left expression must be greater than or equal to right. |
| 7 | 9 | Enabled | root/group[futures\|any]/group[futures\|all] | ( daily high - daily open ) > ( daily open - daily low ) | Inequality test: left expression must be strictly greater than right. |
| 8 | 11 | Enabled | root/group[futures\|any]/group[futures\|all] | ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( daily high - ( ( daily high - daily low ) * 0.618 ) ) | Inequality test: left expression must be greater than or equal to right. |
| 9 | 12 | Enabled | root/group[futures\|any]/group[futures\|all] | ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( daily high - ( ( daily high - daily low ) * 0.618 ) ) ) <= ( daily high * 0.001 ) | Inequality test: left expression must be less than or equal to right. |
| 10 | 13 | Enabled | root/group[futures\|any]/group[futures\|all] | daily high >= ( 1 day ago close * 1.015 ) | Inequality test: left expression must be greater than or equal to right. |
| 11 | 14 | Enabled | root/group[futures\|any]/group[futures\|all] | ( daily high - daily open ) > ( daily open - daily low ) | Inequality test: left expression must be strictly greater than right. |
| 12 | 16 | Enabled | root/group[futures\|any]/group[futures\|all] | ( ( daily high - ( ( daily high - daily low ) * 0.382 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) | Inequality test: left expression must be greater than or equal to right. |
| 13 | 17 | Enabled | root/group[futures\|any]/group[futures\|all] | ( ( daily high - ( ( daily high - daily low ) * 0.382 ) ) - ( ( 1 day ago high + 1 day ago low + daily close ) / 3 ) ) <= ( daily high * 0.001 ) | Inequality test: left expression must be less than or equal to right. |
| 14 | 18 | Enabled | root/group[futures\|any]/group[futures\|all] | daily low <= ( 1 day ago close * 0.985 ) | Inequality test: left expression must be less than or equal to right. |
| 15 | 19 | Enabled | root/group[futures\|any]/group[futures\|all] | ( daily high - daily open ) < ( daily open - daily low ) | Inequality test: left expression must be strictly less than right. |
| 16 | 21 | Enabled | root/group[futures\|any]/group[futures\|all] | ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( daily high - ( ( daily high - daily low ) * 0.382 ) ) | Inequality test: left expression must be greater than or equal to right. |
| 17 | 22 | Enabled | root/group[futures\|any]/group[futures\|all] | ( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( daily high - ( ( daily high - daily low ) * 0.382 ) ) ) <= ( daily high * 0.001 ) | Inequality test: left expression must be less than or equal to right. |
| 18 | 23 | Enabled | root/group[futures\|any]/group[futures\|all] | daily low <= ( 1 day ago close * 0.985 ) | Inequality test: left expression must be less than or equal to right. |
| 19 | 24 | Enabled | root/group[futures\|any]/group[futures\|all] | ( daily high - daily open ) < ( daily open - daily low ) | Inequality test: left expression must be strictly less than right. |
| 20 | 25 | Enabled | root | ( daily high - ( ( daily high - daily low ) * 0.382 ) ) - ( daily high - ( ( daily high - daily low ) * 0.618 ) ) >= ( daily high * 0.006 ) | Inequality test: left expression must be greater than or equal to right. |

## How the enabled logic works

Root group join is **AND (all must pass)**. Nested groups preserve their own AND/OR scope in the rendered source tree; the leaf table names each condition's group scope.
There are **20** enabled leaf conditions. Disabled conditions are ignored at runtime.

Role of each enabled condition:
- **#1** `daily close > 100` — Inequality test: left expression must be strictly greater than right.
- **#2** `daily close < 5000` — Inequality test: left expression must be strictly less than right.
- **#3** `daily volume > 100000` — Inequality test: left expression must be strictly greater than right. Volume condition gates participation/liquidity.
- **#6** `( ( daily high - ( ( daily high - daily low ) * 0.618 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 )` — Inequality test: left expression must be greater than or equal to right.
- **#7** `( ( daily high - ( ( daily high - daily low ) * 0.618 ) ) - ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) <= ( daily high * 0.001 )` — Inequality test: left expression must be less than or equal to right.
- **#8** `daily high >= ( 1 day ago close * 1.015 )` — Inequality test: left expression must be greater than or equal to right.
- **#9** `( daily high - daily open ) > ( daily open - daily low )` — Inequality test: left expression must be strictly greater than right.
- **#11** `( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( daily high - ( ( daily high - daily low ) * 0.618 ) )` — Inequality test: left expression must be greater than or equal to right.
- **#12** `( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( daily high - ( ( daily high - daily low ) * 0.618 ) ) ) <= ( daily high * 0.001 )` — Inequality test: left expression must be less than or equal to right.
- **#13** `daily high >= ( 1 day ago close * 1.015 )` — Inequality test: left expression must be greater than or equal to right.
- **#14** `( daily high - daily open ) > ( daily open - daily low )` — Inequality test: left expression must be strictly greater than right.
- **#16** `( ( daily high - ( ( daily high - daily low ) * 0.382 ) ) ) >= ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 )` — Inequality test: left expression must be greater than or equal to right.
- **#17** `( ( daily high - ( ( daily high - daily low ) * 0.382 ) ) - ( ( 1 day ago high + 1 day ago low + daily close ) / 3 ) ) <= ( daily high * 0.001 )` — Inequality test: left expression must be less than or equal to right.
- **#18** `daily low <= ( 1 day ago close * 0.985 )` — Inequality test: left expression must be less than or equal to right.
- **#19** `( daily high - daily open ) < ( daily open - daily low )` — Inequality test: left expression must be strictly less than right.
- **#21** `( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) ) >= ( daily high - ( ( daily high - daily low ) * 0.382 ) )` — Inequality test: left expression must be greater than or equal to right.
- **#22** `( ( ( 1 day ago high + 1 day ago low + 1 day ago close ) / 3 ) - ( daily high - ( ( daily high - daily low ) * 0.382 ) ) ) <= ( daily high * 0.001 )` — Inequality test: left expression must be less than or equal to right.
- **#23** `daily low <= ( 1 day ago close * 0.985 )` — Inequality test: left expression must be less than or equal to right.
- **#24** `( daily high - daily open ) < ( daily open - daily low )` — Inequality test: left expression must be strictly less than right.
- **#25** `( daily high - ( ( daily high - daily low ) * 0.382 ) ) - ( daily high - ( ( daily high - daily low ) * 0.618 ) ) >= ( daily high * 0.006 )` — Inequality test: left expression must be greater than or equal to right.

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
- `high` — appears 39 time(s) in the expression tree
- `low` — appears 24 time(s) in the expression tree
- `close` — appears 14 time(s) in the expression tree
- `open` — appears 8 time(s) in the expression tree
- `volume` — appears 1 time(s) in the expression tree

### Operators observed
- `+` — 8 occurrence(s)
- `>=` — 7 occurrence(s)
- `<=` — 6 occurrence(s)
- `>` — 4 occurrence(s)
- `<` — 3 occurrence(s)
- `-` — 1 occurrence(s)

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
- Timeframe tokens: `0_days_ago`, `1_days_ago`

## How to use it

- **Horizon context:** treat as **Swing** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.
- **Universe:** results are scoped to **futures**. Liquidity and index membership still vary inside that set.
- **Method context:** Volume/delivery.
- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.
- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.
- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.
- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.
- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.

## Strengths

- Explicit, machine-readable condition tree with **20** active filters — transparent screening logic.
- Universe pinned to **futures**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).
- Participation filters help de-emphasise thin prints that only move on tiny size.
- AND-combined root group increases selectivity versus single-condition scans.

## Limitations and false-signal risks

- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.
- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.
- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.
- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.
- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits.

## Classification and related concepts

- **Horizon:** Swing
- **Methods:** Volume/delivery
- **Tags:** universe:futures, indicator:volume, timeframe:daily
- **Root universe:** futures
- **Root join:** all
- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.

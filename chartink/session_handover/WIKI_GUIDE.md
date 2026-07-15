# Wiki Authoring Guide

This guide explains how to turn a verified Chartink source capture into a detailed wiki page. `TASK_SPEC.md` is the binding requirements document; this file is the practical authoring playbook.

## Page skeleton

Start with `docs/scan-wiki/_template.md`. A completed page follows this shape:

```md
---
scan_id: "<stable Chartink ID>"
scan_name: "<exact displayed name>"
source_url: "<canonical URL>"
market: Indian equities
horizon: "Intraday | Swing | Positional | Multi-horizon | Unspecified"
classification: ["<method>"]
tags: ["<context>"]
captured_at: "YYYY-MM-DDTHH:MM:SS+05:30"
enabled_filter_count: 0
disabled_filter_count: 0
---

# <exact displayed name>

## Source

## What this scan is for

## Exact Chartink scan definition
```text
<VERBATIM source capture>
```

## Filter status and interpretation
| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|

## How the enabled logic works

## Disabled filters

## Calculation notes

## How to use it

## Strengths

## Limitations and false-signal risks

## Classification and related concepts
```

Do not put commentary, normalisation, or assistant annotations inside the verbatim block. If a screenshot proves the UI state, link or describe it outside the source block.

## Recording enabled and disabled filters

Add one table row for each independent filter, in the source display order. The `Original filter (verbatim)` cell must retain the actual condition unchanged. For nested groups, preserve the group context or add only a short group-path label; do not rewrite the condition.

Illustrative format only (not asserted Chartink syntax):

| # | Status | Original filter (verbatim) | What it calculates / means |
|---:|---|---|---|
| 1 | Enabled | `close > sma(close, 20)` | Tests whether current close is above its 20-period simple moving average. |
| 2 | Disabled | `volume > sma(volume, 20) * 2` | If enabled, it would require a volume expansion and likely reduce candidates. |

If state cannot be determined reliably, use `Needs review`. Record why, retain the source evidence, and include the exception in index reconciliation. Never silently label an uncertain filter enabled or disabled.

## Writing each explanatory section

### What this scan is for

Describe the probable screening objective in plain language. Use cautious language such as "This appears designed to identify ..." when intent comes only from conditions or title. State the market behaviour screened for, not a promise of a profitable outcome.

### How the enabled logic works

Explain each active condition and then its intersection with the others. Cover the trend regime/price location, trigger event, participation or liquidity gates, overextension/risk gates, and the effect of AND/OR grouping on candidate count. Distinguish confirmation filters from the core trigger.

### Calculation notes

Explain formulas and inputs only as needed by that scan:

- **SMA(n)**: arithmetic average over `n` observations.
- **EMA(n)**: exponentially weighted moving average, emphasizing recent observations.
- **RSI(n)**: momentum oscillator built from average gains and losses; state threshold and comparison direction.
- **MACD**: difference between fast and slow EMAs with a signal line; state all displayed parameters and whether the scan uses level, crossover, or histogram behavior.
- **ATR(n)**: smoothed true range, a volatility measure rather than directional signal.
- **Bollinger Bands**: moving average plus/minus a configured standard-deviation multiple.

State exact period, price field, offset, aggregation, and comparator from the source. Do not guess Chartink-specific time aggregation, delivery data, or operator semantics: consult official documentation or label the uncertainty.

### Disabled filters

Document each disabled condition separately. Explain:

1. its verbatim condition;
2. what confirmation/exclusion it would add if enabled;
3. likely effect on selectivity, timing, and candidate count;
4. trade-offs, including missed early moves or fewer false signals.

Do not claim the creator's reason for disabling it unless source metadata says so. Phrase unverified intent as an inference.

### How to use it

Make this educational and conditional. Address likely horizon/candle periodicity only when supported, liquid Indian-equity universe suitability, useful confirmation context, possibility of late signals, possible invalidation/risk framing, and operational risks such as gaps, low liquidity, corporate events, and end-of-day versus intraday timing. Avoid personalised sizing, buy/sell instructions, or performance guarantees.

### Strengths and limitations

Tie every point to actual scan logic. For example, breakout plus relative volume can filter quiet ranges but still produce news-driven false breakouts; mean-reversion conditions can help in ranges but may repeatedly fight a strong trend; moving-average scans are interpretable but lag reversals and whipsaw sideways. Do not paste a generic pro/con list across unrelated scans.

## Classification rules

Use multiple labels where appropriate. Suggested mapping:

| Dominant condition | Suitable method tags |
|---|---|
| New high, resistance break, range escape | Breakout, Momentum, Price action |
| Price relative to moving average or MA crossover/slope | Trend following, Moving average |
| RSI, MACD, Stochastic, ROC thresholds | Oscillator; Momentum or Mean reversion as direction warrants |
| Band squeeze/expansion, ATR, range contraction | Volatility plus Breakout or Mean reversion if supported |
| Volume, delivery, VWAP, liquidity | Volume/delivery plus actual trigger method |
| Candlestick, pivot, support/resistance patterns | Price action, Support/resistance |
| Valuation or financial ratios | Fundamental |

Use `Multi-factor` only when the deliberate combination is central and no single method describes the scan adequately. Choose the primary index category from the decisive trigger rather than a routine confirmation filter.

## Index maintenance

Keep `docs/scan-wiki/README.md` as a linked Markdown index:

| ID | Scan | Horizon | Primary classification | Enabled | Disabled | Source |
|---|---|---|---|---:|---:|---|

Link scan name to its page and source to the Chartink URL where appropriate. Include progress counts: dashboard total, inventoried, raw-captured, fully documented, needs-review, and inaccessible. Update these counts after each batch.

## Quality checklist

Before marking a page complete, verify:

- [ ] ID, title, URL, and capture timestamp match raw data.
- [ ] Verbatim definition is non-empty and source-faithful.
- [ ] Every filter has exactly one status-table row.
- [ ] Enabled + disabled + needs-review reconciles to total filters.
- [ ] Every disabled filter is included in source, table, and disabled-filter analysis.
- [ ] Boolean groups, offsets, values, periods, price fields, and comparators remain intact.
- [ ] Classification/horizon is evidence-based or marked uncertain.
- [ ] Calculations, use, and risks are scan-specific.
- [ ] No prose claims guaranteed performance or alters source logic.

## Batch strategy for approximately 500 scans

Capture source in manageable batches and save it immediately. For each batch: inventory, raw capture, count/state QA, page generation, page QA, and index update. Keep raw captures immutable. If a scan later changes on Chartink, create a new timestamped capture/version rather than overwriting historical source evidence.

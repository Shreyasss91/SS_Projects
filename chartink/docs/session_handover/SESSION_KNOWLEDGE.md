# Session Knowledge

## User request

The user has nearly 500 Chartink scans. They want every scan enumerated, classified, and converted into a detailed wiki. They explicitly require every enabled and disabled filter to be included and each filter's state to be stated. They also require a section that reproduces the entire scan exactly as it is written, including both enabled and disabled filters.

The wiki must explain purpose, use cases, calculation method, advantages, disadvantages, practical usage, and relevant cautions. The corpus spans Indian-equity intraday, swing, and positional scans.

## Documentation model

There is one Markdown page per scan plus a root Markdown index. The source snapshot and the analysis must remain visibly separate. The page template is `docs/scan-wiki/_template.md` and must retain these sections:

1. YAML metadata.
2. Source metadata.
3. Plain-language purpose.
4. Exact Chartink scan definition in a fenced `text` block.
5. Ordered filter-status and interpretation table.
6. How the enabled logic works together.
7. Disabled filters and the impact of enabling each.
8. Calculation notes.
9. How to use it.
10. Strengths.
11. Limitations and false-signal risks.
12. Classification and related concepts.

Front matter should contain the stable scan ID, exact name, source URL, market, horizon, classification, tags, capture timestamp, and enabled/disabled filter counts.

## Capture facts required before analysis

For each scan capture, retain:

- dashboard order, stable scan ID, exact display name, canonical URL, and visible description;
- all result-affecting scan-level settings such as universe, periodicity, and sorting if visible;
- the complete condition tree exactly as displayed, including groups, AND/OR relationships, parentheses, fields, periods, offsets, thresholds, and comparison operators;
- every filter's exact wording, display order, group relationship, and UI status: `Enabled`, `Disabled`, or `Needs review` if genuinely ambiguous;
- capture timestamp and, when useful, a screenshot or source snapshot that proves the visual status.

Do not infer disabled filters from missing expressions. Do not convert source syntax to prose inside the exact-definition block. Do not reorder conditions.

## Classification vocabulary

Apply multiple tags when warranted. Do not force a single label.

- Horizons: `Intraday`, `Swing`, `Positional`, `Multi-horizon`, `Unspecified`, `Needs review`.
- Methods: `Breakout`, `Trend following`, `Momentum`, `Mean reversion`, `Volume/delivery`, `Price action`, `Moving average`, `Oscillator`, `Volatility`, `Support/resistance`, `Fundamental`, `Multi-factor`, `Other`.
- Context tags: long/short bias, index or stock universe, liquidity/market-cap constraints, and indicator families such as RSI, MACD, ADX, ATR, Bollinger Bands, moving averages, pivots, candlesticks, VWAP, volume, or delivery.

Only assign a horizon when evidence supports it. A short lookback is not enough to prove intraday intent. Use uncertainty labels rather than inventing intent.

## Analysis conventions

- Explain each active condition and the combined boolean logic. An AND group is more selective; OR groups broaden candidates.
- Define calculations at formula/input level when needed: indicator period, price field, comparison direction, crossover, offset, aggregation, and threshold.
- If Chartink-specific semantics are not known from the source or official Chartink documentation, say so rather than guessing.
- Discuss regimes where a setup may help and regimes where it may fail: trends/ranges, gaps/news, low liquidity, index effects, parameter sensitivity, delayed data, and late signals as applicable.
- Frame entries, confirmation, exits, stops, and position sizing as educational considerations, never personal financial advice or guaranteed results.
- Treat reasoning about a disabled filter as inference unless the scan description states the creator's intent. Use phrases such as "would likely add" rather than claiming why it was disabled.

## Technical history

The previous session created the scaffold but had no browser-control tool. A local Chrome-process inspection failed due Windows account/SID isolation. This confirms only that the environment could not attach to Chrome; it does not imply a Chartink access problem. No credentials, cookies, screenshots, HTML exports, scan definitions, or other raw source data have been added to the repository.

The user has been instructed to use the ChatGPT desktop app's Chrome plugin/extension. The new session may have a `@Chrome` capability or may need to ask the user for a manual/exported source capture instead. Credentials must not be requested.

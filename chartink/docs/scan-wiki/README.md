# Chartink Scan Wiki

This knowledge base documents the Chartink scans exactly as captured from the
account dashboard. It covers Indian-equity scans used for intraday, swing, and
positional workflows.

## Preservation rules

Each scan page preserves the source scan separately from its analysis:

- The `Exact Chartink scan definition` section is a verbatim capture of the
  entire scan, in original order and wording.
- Every filter is recorded, whether it is enabled or disabled.
- A filter's enabled/disabled state is recorded explicitly in the filter-status
  table, as the textual definition alone may not retain Chartink's visual state.
- Interpretation, classification, and trading notes never alter the captured
  definition.

## Scan index

| ID | Scan | Horizon | Primary classification | Enabled | Disabled | Source |
|---|---|---|---|---:|---:|---|

This table will be populated from the dashboard capture. Individual pages will
use a stable ID-based filename and may be placed in a category folder without
changing their source identity.

## Classification vocabulary

- Horizon: Intraday, Swing, Positional, or Multi-horizon
- Method: Breakout, Trend following, Momentum, Mean reversion, Volume/
  delivery, Price action, Moving average, Oscillator, Volatility,
  Support/resistance, Fundamental, Multi-factor, or Other
- Context tags: long/short bias, market-cap or liquidity universe, index/stock
  universe, and indicator families used

## Page format

Use [the scan template](_template.md) for every captured scan. The source is
captured before analysis is written, so an interrupted documentation run never
loses the original scan logic.

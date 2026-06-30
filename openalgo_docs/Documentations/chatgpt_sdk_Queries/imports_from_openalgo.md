
# OpenAlgo – What Can Be Imported From `openalgo`

## Short Answer

The OpenAlgo documentation explicitly shows:

```python
from openalgo import api
from openalgo import ta
```

These are the two primary public imports documented throughout the SDK and indicator documentation.

---

# 1. `api`

## Purpose

Used for:

- Authentication
- Market Data
- Historical Data
- Orders
- Option Chain
- Expiry Discovery
- Holdings
- Funds
- Position Book
- Trade Book
- Order Book
- Holidays
- WebSocket Streaming

---

## Import

```python
from openalgo import api
```

---

## Client Creation

### REST Only

```python
client = api(
    api_key=api_key,
    host=host
)
```

---

### REST + WebSocket

```python
client = api(
    api_key=api_key,
    host=host,
    ws_url=ws_url,
    verbose=False
)
```

---

## What `api` Gives You

Creates:

```python
client
```

which exposes methods such as:

```python
client.history()

client.quotes()

client.depth()

client.optionchain()

client.expiry()

client.placeorder()

client.optionsorder()

client.modifyorder()

client.cancelorder()

client.closeposition()

client.orderbook()

client.tradebook()

client.positionbook()

client.holdings()

client.funds()

client.search()

client.symbol()

client.holidays()

client.subscribe_ltp()

client.unsubscribe_ltp()

client.subscribe_quote()

client.unsubscribe_quote()

client.subscribe_depth()

client.unsubscribe_depth()

client.disconnect()
```

---

# 2. `ta`

## Purpose

Technical Analysis Library

Contains all documented OpenAlgo indicators and utility functions.

---

## Import

```python
from openalgo import ta
```

---

# TREND INDICATORS

---

## SMA

```python
ta.sma(close, length)
```

Returns:

```python
Series
```

---

## EMA

```python
ta.ema(close, length)
```

Returns:

```python
Series
```

---

## WMA

```python
ta.wma(close, length)
```

Returns:

```python
Series
```

---

## HMA

```python
ta.hma(close, length)
```

Returns:

```python
Series
```

---

## DEMA

```python
ta.dema(close, length)
```

Returns:

```python
Series
```

---

## TEMA

```python
ta.tema(close, length)
```

Returns:

```python
Series
```

---

## VWMA

```python
ta.vwma(close, volume, length)
```

Returns:

```python
Series
```

---

## Supertrend

```python
ta.supertrend(
    high,
    low,
    close,
    period,
    multiplier
)
```

Returns:

```python
supertrend
direction
```

---

## Ichimoku

```python
ta.ichimoku(
    high,
    low,
    close
)
```

Returns:

```python
conversion
base
span_a
span_b
lagging
```

---

# MOMENTUM INDICATORS

---

## RSI

```python
ta.rsi(close, length)
```

---

## MACD

```python
ta.macd(
    close,
    fast,
    slow,
    signal
)
```

Returns:

```python
macd
signal
histogram
```

---

## Stochastic

```python
ta.stochastic(
    high,
    low,
    close,
    k_period,
    d_period
)
```

Returns:

```python
percent_k
percent_d
```

---

## CCI

```python
ta.cci(
    high,
    low,
    close,
    length
)
```

---

## Williams %R

```python
ta.williamsr(
    high,
    low,
    close,
    length
)
```

---

## ROC

```python
ta.roc(
    close,
    length
)
```

---

# VOLATILITY INDICATORS

---

## ATR

```python
ta.atr(
    high,
    low,
    close,
    length
)
```

---

## Bollinger Bands

```python
ta.bbands(
    close,
    length,
    std
)
```

Returns:

```python
upper
middle
lower
```

---

## Keltner Channel

```python
ta.keltner(
    high,
    low,
    close,
    length
)
```

Returns:

```python
upper
middle
lower
```

---

## Donchian Channel

```python
ta.donchian(
    high,
    low,
    length
)
```

Returns:

```python
upper
middle
lower
```

---

# VOLUME INDICATORS

---

## OBV

```python
ta.obv(
    close,
    volume
)
```

---

## VWAP

```python
ta.vwap(
    high,
    low,
    close,
    volume
)
```

---

## MFI

```python
ta.mfi(
    high,
    low,
    close,
    volume,
    length
)
```

---

## ADL

```python
ta.adl(
    high,
    low,
    close,
    volume
)
```

---

## CMF

```python
ta.cmf(
    high,
    low,
    close,
    volume,
    length
)
```

---

## RVOL

```python
ta.rvol(
    volume,
    length
)
```

---

# STATISTICAL INDICATORS

---

## Linear Regression

```python
ta.linearreg(
    close,
    length
)
```

---

## Slope

```python
ta.slope(
    close,
    length
)
```

---

## Correlation

```python
ta.correlation(
    series1,
    series2,
    length
)
```

---

## Beta

```python
ta.beta(
    asset_returns,
    benchmark_returns,
    length
)
```

---

## Variance

```python
ta.variance(
    close,
    length
)
```

---

## Standard Deviation

```python
ta.stddev(
    close,
    length
)
```

---

# HYBRID INDICATORS

---

## ADX

```python
ta.adx(
    high,
    low,
    close,
    length
)
```

Returns:

```python
adx
plus_di
minus_di
```

---

## Aroon

```python
ta.aroon(
    high,
    low,
    length
)
```

Returns:

```python
aroon_up
aroon_down
```

---

## Pivot Points

```python
ta.pivots(
    high,
    low,
    close
)
```

Returns:

```python
pivot
r1
r2
r3
s1
s2
s3
```

---

## Parabolic SAR

```python
ta.psar(
    high,
    low
)
```

---

# UTILITY FUNCTIONS

---

## crossover

```python
ta.crossover(
    fast_series,
    slow_series
)
```

Returns:

```python
Boolean Series
```

---

## crossunder

```python
ta.crossunder(
    fast_series,
    slow_series
)
```

Returns:

```python
Boolean Series
```

---

## cross

```python
ta.cross(
    series1,
    series2
)
```

Returns:

```python
Boolean Series
```

---

## highest

```python
ta.highest(
    series,
    length
)
```

---

## lowest

```python
ta.lowest(
    series,
    length
)
```

---

## change

```python
ta.change(
    series
)
```

---

## roc

```python
ta.roc(
    series,
    length
)
```

---

# Documented Public Imports

The OpenAlgo documentation consistently documents:

```python
from openalgo import api
from openalgo import ta
```

and all examples throughout the SDK, indicators, WebSocket, strategy hosting, and order-management documentation are built around these two imports.

---

# Can Anything Else Be Imported?

The loaded OpenAlgo documentation does **not explicitly document** additional public imports such as:

```python
from openalgo import indicators
from openalgo import websocket
from openalgo import strategy
from openalgo import utils
```

Therefore, based strictly on the documented SDK surface, the officially documented imports are:

```python
from openalgo import api
from openalgo import ta
```

with:

```python
api
```

providing all broker, market-data, order-management, option-discovery, holiday, portfolio and WebSocket functionality, and:

```python
ta
```

providing all documented technical indicators, statistical indicators, volume indicators, hybrid indicators, and utility signal-generation functions.
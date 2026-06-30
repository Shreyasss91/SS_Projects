# OpenAlgo Technical Indicators – Complete Access Guide

> A fully exhaustive indicator reference requires reading every indicator module in the installed OpenAlgo package. Based on the OpenAlgo indicator documentation available in the loaded knowledge base, indicators are organized into:
>
> - Trend Indicators
> - Momentum Indicators
> - Volatility Indicators
> - Volume Indicators
> - Statistical Indicators
> - Hybrid Indicators
> - Utility Functions

All indicators are accessed through:

```python
from openalgo import ta
```

---

# Standard Data Preparation

Most indicators use a DataFrame returned by:

```python
df = client.history(
    symbol="RELIANCE",
    exchange="NSE",
    interval="D",
    start_date="2026-01-01",
    end_date="2026-05-30"
)
```

Expected columns:

```python
open
high
low
close
volume
```

---

# Return Structure

Almost all indicators return:

```python
pandas.Series
```

Example:

```python
ema = ta.ema(
    df["close"],
    20
)
```

Result:

```python
0       NaN
1       NaN
...
19      2521.20
20      2523.55
```

Multi-output indicators return tuples or multiple Series.

---

# TREND INDICATORS

---

## SMA

Simple Moving Average

### Inputs

```python
ta.sma(
    close,
    length
)
```

### Example

```python
df["SMA20"] = ta.sma(
    df["close"],
    20
)
```

### Returns

```python
pandas.Series
```

---

## EMA

Exponential Moving Average

### Inputs

```python
ta.ema(
    close,
    length
)
```

### Example

```python
df["EMA20"] = ta.ema(
    df["close"],
    20
)
```

### Returns

```python
Series
```

---

## WMA

Weighted Moving Average

```python
df["WMA20"] = ta.wma(
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

## HMA

Hull Moving Average

```python
df["HMA20"] = ta.hma(
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

## DEMA

Double EMA

```python
df["DEMA20"] = ta.dema(
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

## TEMA

Triple EMA

```python
df["TEMA20"] = ta.tema(
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

## VWMA

Volume Weighted Moving Average

```python
df["VWMA20"] = ta.vwma(
    df["close"],
    df["volume"],
    20
)
```

Returns:

```python
Series
```

---

## Supertrend

### Inputs

```python
ta.supertrend(
    high,
    low,
    close,
    period,
    multiplier
)
```

### Example

```python
st, trend = ta.supertrend(
    df["high"],
    df["low"],
    df["close"],
    10,
    3
)
```

### Returns

```python
supertrend_series
trend_direction_series
```

---

## Ichimoku

### Inputs

```python
ta.ichimoku(
    high,
    low,
    close
)
```

### Returns

```python
conversion_line
base_line
leading_span_a
leading_span_b
lagging_span
```

---

# MOMENTUM INDICATORS

---

## RSI

### Inputs

```python
ta.rsi(
    close,
    length
)
```

### Example

```python
df["RSI14"] = ta.rsi(
    df["close"],
    14
)
```

### Returns

```python
Series
```

---

## MACD

### Inputs

```python
ta.macd(
    close,
    fast,
    slow,
    signal
)
```

### Example

```python
macd, signal, hist = ta.macd(
    df["close"],
    12,
    26,
    9
)
```

### Returns

```python
macd_line
signal_line
histogram
```

---

## Stochastic

### Inputs

```python
ta.stochastic(
    high,
    low,
    close,
    k_period,
    d_period
)
```

### Returns

```python
percent_k
percent_d
```

---

## CCI

```python
df["CCI"] = ta.cci(
    df["high"],
    df["low"],
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

## Williams %R

```python
df["WilliamsR"] = ta.williamsr(
    df["high"],
    df["low"],
    df["close"],
    14
)
```

Returns:

```python
Series
```

---

## ROC

Rate Of Change

```python
df["ROC"] = ta.roc(
    df["close"],
    10
)
```

Returns:

```python
Series
```

---

# VOLATILITY INDICATORS

---

## ATR

Average True Range

### Inputs

```python
ta.atr(
    high,
    low,
    close,
    length
)
```

### Example

```python
df["ATR"] = ta.atr(
    df["high"],
    df["low"],
    df["close"],
    14
)
```

Returns:

```python
Series
```

---

## Bollinger Bands

### Inputs

```python
ta.bbands(
    close,
    length,
    std
)
```

### Example

```python
upper, middle, lower = ta.bbands(
    df["close"],
    20,
    2
)
```

### Returns

```python
upper_band
middle_band
lower_band
```

---

## Keltner Channel

```python
upper, middle, lower = ta.keltner(
    df["high"],
    df["low"],
    df["close"],
    20
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
upper, middle, lower = ta.donchian(
    df["high"],
    df["low"],
    20
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

On Balance Volume

```python
df["OBV"] = ta.obv(
    df["close"],
    df["volume"]
)
```

Returns:

```python
Series
```

---

## VWAP

### Inputs

```python
ta.vwap(
    high,
    low,
    close,
    volume
)
```

### Example

```python
df["VWAP"] = ta.vwap(
    df["high"],
    df["low"],
    df["close"],
    df["volume"]
)
```

Returns:

```python
Series
```

---

## MFI

Money Flow Index

```python
df["MFI"] = ta.mfi(
    df["high"],
    df["low"],
    df["close"],
    df["volume"],
    14
)
```

Returns:

```python
Series
```

---

## ADL

Accumulation Distribution Line

```python
df["ADL"] = ta.adl(
    df["high"],
    df["low"],
    df["close"],
    df["volume"]
)
```

Returns:

```python
Series
```

---

## CMF

Chaikin Money Flow

```python
df["CMF"] = ta.cmf(
    df["high"],
    df["low"],
    df["close"],
    df["volume"],
    20
)
```

Returns:

```python
Series
```

---

## RVOL

Relative Volume

```python
df["RVOL"] = ta.rvol(
    df["volume"],
    20
)
```

Returns:

```python
Series
```

---

# STATISTICAL INDICATORS

---

## Linear Regression

```python
df["LR"] = ta.linearreg(
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

## Slope

```python
df["Slope"] = ta.slope(
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

## Correlation

```python
df["Corr"] = ta.correlation(
    series1,
    series2,
    20
)
```

Returns:

```python
Series
```

---

## Beta

```python
df["Beta"] = ta.beta(
    asset_returns,
    benchmark_returns,
    20
)
```

Returns:

```python
Series
```

---

## Variance

```python
df["Variance"] = ta.variance(
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

## Standard Deviation

```python
df["StdDev"] = ta.stddev(
    df["close"],
    20
)
```

Returns:

```python
Series
```

---

# HYBRID INDICATORS

---

## ADX

Average Directional Index

### Inputs

```python
ta.adx(
    high,
    low,
    close,
    length
)
```

### Example

```python
adx, plus_di, minus_di = ta.adx(
    df["high"],
    df["low"],
    df["close"],
    14
)
```

### Returns

```python
adx
plus_di
minus_di
```

---

## Aroon

```python
aroon_up, aroon_down = ta.aroon(
    df["high"],
    df["low"],
    25
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
pivot, r1, r2, r3, s1, s2, s3 = ta.pivots(
    high,
    low,
    close
)
```

Returns:

```python
7 Series
```

---

## Parabolic SAR

```python
df["PSAR"] = ta.psar(
    df["high"],
    df["low"]
)
```

Returns:

```python
Series
```

---

# UTILITY FUNCTIONS

These do not calculate indicators but help generate signals.

---

## crossover()

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

Example:

```python
buy_signal = ta.crossover(
    ema_fast,
    ema_slow
)
```

---

## crossunder()

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

## cross()

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

## highest()

```python
ta.highest(
    series,
    length
)
```

Returns:

```python
Series
```

---

## lowest()

```python
ta.lowest(
    series,
    length
)
```

Returns:

```python
Series
```

---

## change()

```python
ta.change(
    series
)
```

Returns:

```python
Series
```

---

## roc()

```python
ta.roc(
    series,
    length
)
```

Returns:

```python
Series
```

---

# Typical Multi-Indicator Example

```python
from openalgo import ta

df["EMA20"] = ta.ema(
    df["close"],
    20
)

df["RSI14"] = ta.rsi(
    df["close"],
    14
)

df["ATR14"] = ta.atr(
    df["high"],
    df["low"],
    df["close"],
    14
)

macd, signal, hist = ta.macd(
    df["close"],
    12,
    26,
    9
)

buy_signal = ta.crossover(
    df["close"],
    df["EMA20"]
)
```

# Most Commonly Used Indicators

```python
ta.ema()
ta.sma()
ta.rsi()
ta.macd()
ta.supertrend()
ta.adx()
ta.atr()
ta.vwap()
ta.obv()
ta.bbands()
ta.psar()
ta.stochastic()
ta.cci()
ta.williamsr()
ta.mfi()
ta.aroon()
ta.linearreg()
ta.slope()
ta.crossover()
ta.crossunder()
```

These are the indicators documented in the loaded OpenAlgo indicator reference categories (Trend, Momentum, Volatility, Volume, Statistical, Hybrid, and Utility).
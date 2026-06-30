Appendix A
OpenAlgo Technical Indicators Reference

Volume I
===========================
A.1 Introduction
A.2 Indicator Conventions
A.3 Input Types
A.4 Return Types
A.5 Warm-up Behavior
A.6 Missing Values
A.7 Performance Notes
A.8 TA-Lib Compatibility
A.9 PineScript Compatibility

Volume II
===========================
Trend Indicators

SMA
EMA
WMA
DEMA
TEMA
TRIMA
KAMA
HMA
SuperTrend
Parabolic SAR
...

Volume III
===========================
Momentum Indicators

RSI
MACD
ROC
ROCP
ROCR
ROCR100
MOM
PPO
APO
CMO
...

Volume IV
===========================
Oscillators

CCI
Williams %R
Stochastic
Stochastic Fast
...

Volume V
===========================
Volatility Indicators

ATR
True Range
Bollinger Bands
Standard Deviation
Variance
...

Volume VI
===========================
Volume Indicators

OBV
AD
ADOSC
MFI
...

Volume VII
===========================
Directional Movement

+DM
-DM
DX
ADX
ADXR

Volume VIII
===========================
Regression & Statistics

Linear Regression
Regression Angle
Regression Intercept
TSF
Correlation
Covariance
StdDev
Variance
...

Volume IX
===========================
Price Transform Indicators

Typical Price
Median Price
Average Price
Weighted Close
Midpoint
Midprice
...

Volume X
===========================
Utility Functions

Highest
Lowest
Rolling Max
Rolling Min
Rolling Mean
Rolling Sum
...


















Every Indicator Should Have The Same Layout

This consistency makes it excellent for both developers and LLMs.
Example:
# RSI (Relative Strength Index)

---

## Purpose

Measures momentum by comparing recent gains and losses.

Category

Momentum

---

## Mathematical Concept

RSI oscillates between 0 and 100.

High values indicate strong buying pressure.

Low values indicate strong selling pressure.

---

## Typical Uses

- Overbought detection
- Oversold detection
- Divergence
- Trend confirmation

---

## Function

```python
ta.rsi(close, period=14)
```

---

## Parameters

close

NumPy array

Required

period

Integer

Default = 14

---

## Returns

NumPy array

Length equals input length.

---

## Example

```python
rsi = ta.rsi(close)
```

---

## Interpretation

RSI > 70

Possible overbought condition.

RSI < 30

Possible oversold condition.

---

## Advantages

- Simple
- Fast
- Well understood

---

## Limitations

Produces false signals in strong trends.

---

## Computational Complexity

O(n)

---

## Compatible With

EMA

MACD

ATR

SuperTrend

---

## Not Recommended With

Multiple momentum oscillators measuring identical behavior.

---

## TA-Lib Compatibility

Compatible.

---

## PineScript Compatibility

Equivalent calculation.

Every Indicator Gets Exactly The Same Sections
Purpose

Category

Inputs

Outputs

Parameters

Return Type

Formula Overview

Interpretation

Typical Uses

Advantages

Limitations

Example

Complexity

Warm-up Period

Compatibility

References


Cross References

Every indicator should reference related indicators.

Example:
MACD

See also

EMA
PPO
APO
RSI

Likewise,

ATR

See also

True Range
SuperTrend
Bollinger Bands


Add Comparison Tables

Example

Moving Average Comparison
Indicator	Lag	Smoothness	Adaptive	Typical Use
SMA	High	High	No	Long-term trend
EMA	Medium	Medium	No	Swing trading
WMA	Medium	Lower	No	Short-term trend
DEMA	Low	Medium	No	Faster signals
TEMA	Very Low	Medium	No	Fast trend detection
HMA	Very Low	Smooth	No	Reduced lag
KAMA	Adaptive	Adaptive	Yes	Changing market conditions

Another example

Momentum Comparison
Indicator	Range	Oscillator	Trend Sensitive
RSI	0–100	Yes	Medium
CMO	-100 to 100	Yes	Medium
ROC	Unbounded	No	High
MOM	Unbounded	No	High
MACD	Unbounded	Yes	High
Add Strategy Recipes

Example

Trend Following

EMA

+

SuperTrend

+

ATR Stop
Swing Trading

RSI

+

MACD

+

Volume Confirmation
Breakout

ATR

+

Bollinger Bands

+

Volume Spike
Add Performance Notes

For every indicator

Time Complexity

O(n)

Memory

O(n)

Incremental Update

Supported

Streaming Friendly

Yes
LLM Notes Section

This is the most valuable addition.

Example

When generating OpenAlgo code:

Prefer RSI for momentum.

Prefer ATR for stop-loss.

Do not combine RSI and CMO unless intentionally comparing momentum methods.

Cache RSI if multiple strategies reuse it.

Use NumPy arrays.
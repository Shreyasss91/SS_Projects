# Chartink Scan Wiki

This knowledge base documents the Chartink scans exactly as captured from the
account dashboard export (`data/exports/all_scans_raw.json`). It covers Indian-equity
scans used for intraday, swing, and positional workflows.

## Preservation rules

Each scan page preserves the source scan separately from its analysis:

- The `Exact Chartink scan definition` section is built from the immutable export,
  including every condition from `atlas_json` in display order with explicit
  `[Enabled]` / `[Disabled]` labels (because `atlas_query` alone may omit disabled filters).
- Raw captures live under [`source-snapshots/`](source-snapshots/) (`.json` + `.txt`).
- Interpretation never alters the captured definition.

## Reconciliation

| Metric | Count |
|---|---:|
| Dashboard / export total | 478 |
| Inventoried scans | 478 |
| Wiki pages generated | 478 |
| Raw source snapshots | 478 |
| Fully documented (page + snapshot) | 478 |
| Total enabled leaf filters | 2614 |
| Total disabled leaf filters | 671 |
| Scans with zero enabled leaves or needs-review rows | 0 |
| Inaccessible scans | 0 |

### Horizon distribution

| Horizon | Scans |
|---|---:|
| Swing | 225 |
| Intraday | 195 |
| Multi-horizon | 37 |
| Positional | 20 |
| Unspecified | 1 |

### Primary method distribution

| Primary classification | Scans |
|---|---:|
| Moving average | 91 |
| Volume/delivery | 90 |
| Oscillator | 70 |
| Breakout | 58 |
| Price action | 34 |
| Other | 29 |
| Mean reversion | 24 |
| Volatility | 23 |
| Fundamental | 21 |
| Support/resistance | 20 |
| Momentum | 18 |

## Scan index

| ID | Scan | Horizon | Primary classification | Enabled | Disabled | Source |
|---|---|---|---|---:|---:|---|
| 25376546 | [75 min RSI](scans/25376546--75-min-rsi.md) | Intraday | Oscillator | 4 | 0 | [Chartink](https://chartink.com/screener/75-min-rsi-139) |
| 25372594 | [Ichimoku Cloud Retest Buy](scans/25372594--ichimoku-cloud-retest-buy.md) | Swing | Moving average | 3 | 0 | [Chartink](https://chartink.com/screener/ichimoku-cloud-retest-buy) |
| 25338157 | [For Anchored Vwap](scans/25338157--for-anchored-vwap.md) | Swing | Volatility | 1 | 1 | [Chartink](https://chartink.com/screener/for-anchored-vwap) |
| 25332859 | [ichimoku cloud break scanner](scans/25332859--ichimoku-cloud-break-scanner.md) | Intraday | Moving average | 12 | 0 | [Chartink](https://chartink.com/screener/ichimoku-cloud-break-scanner-2) |
| 25332467 | [ichimoku](scans/25332467--ichimoku.md) | Intraday | Moving average | 10 | 3 | [Chartink](https://chartink.com/screener/ichimoku-17082998) |
| 25310813 | [open=high, open=low reversal](scans/25310813--openhigh-openlow-reversal.md) | Intraday | Price action | 2 | 4 | [Chartink](https://chartink.com/screener/open-high-open-low-reversal) |
| 25267591 | [stocks eod decision](scans/25267591--stocks-eod-decision.md) | Intraday | Moving average | 11 | 4 | [Chartink](https://chartink.com/screener/top-gainer-4-2) |
| 25173278 | [INTRADAY STOCK](scans/25173278--intraday-stock.md) | Intraday | Moving average | 6 | 0 | [Chartink](https://chartink.com/screener/intraday-stock-9123511) |
| 25172547 | [Monthly 2026-01-25](scans/25172547--monthly-2026-01-25.md) | Positional | Moving average | 2 | 1 | [Chartink](https://chartink.com/screener/monthly-2026-01-25-2) |
| 25165131 | [Volume Profile](scans/25165131--volume-profile.md) | Positional | Volume/delivery | 1 | 5 | [Chartink](https://chartink.com/screener/volume-profile-137) |
| 25160374 | [Stocks to short WeeklyTF](scans/25160374--stocks-to-short-weeklytf.md) | Swing | Oscillator | 3 | 8 | [Chartink](https://chartink.com/screener/stocks-to-short-weeklytf) |
| 25160125 | [Stocks to Buy WeeklyTF](scans/25160125--stocks-to-buy-weeklytf.md) | Swing | Oscillator | 9 | 0 | [Chartink](https://chartink.com/screener/stocks-to-buy-weeklytf) |
| 25094589 | [PE ratio](scans/25094589--pe-ratio.md) | Positional | Fundamental | 2 | 0 | [Chartink](https://chartink.com/screener/pe-ratio-445) |
| 25085506 | [Test Custom Indicators](scans/25085506--test-custom-indicators.md) | Multi-horizon | Price action | 6 | 10 | [Chartink](https://chartink.com/screener/test-custom-indicators) |
| 25084558 | [Weakness DTF](scans/25084558--weakness-dtf.md) | Swing | Momentum | 9 | 5 | [Chartink](https://chartink.com/screener/weakness-dtf) |
| 24994470 | [Daily RSI](scans/24994470--daily-rsi.md) | Swing | Oscillator | 2 | 0 | [Chartink](https://chartink.com/screener/daily-rsi-405375) |
| 24991684 | [Heiken Ashi Shortterm Breakout](scans/24991684--heiken-ashi-shortterm-breakout.md) | Swing | Breakout | 2 | 0 | [Chartink](https://chartink.com/screener/heiken-ashi-shortterm-breakout) |
| 24940279 | [Ichimoku Std Deviation](scans/24940279--ichimoku-std-deviation.md) | Intraday | Moving average | 1 | 2 | [Chartink](https://chartink.com/screener/ichimoku-std-deviation) |
| 24799460 | [Monthly VWAP ALERT](scans/24799460--monthly-vwap-alert.md) | Positional | Volume/delivery | 2 | 0 | [Chartink](https://chartink.com/screener/monthly-vwap-alert) |
| 24680518 | [Rolling VWAP](scans/24680518--rolling-vwap.md) | Swing | Volume/delivery | 8 | 0 | [Chartink](https://chartink.com/screener/rolling-vwap-2) |
| 24675484 | [VWMA](scans/24675484--vwma.md) | Intraday | Moving average | 12 | 2 | [Chartink](https://chartink.com/screener/vwma-1020406822) |
| 24661555 | [Opening Cues](scans/24661555--opening-cues.md) | Intraday | Moving average | 2 | 0 | [Chartink](https://chartink.com/screener/opening-cues-3) |
| 24613797 | [ema cloud__FII Data Vishy Bhai Indicator](scans/24613797--ema-cloud__fii-data-vishy-bhai-indicator.md) | Intraday | Moving average | 2 | 0 | [Chartink](https://chartink.com/screener/ema-cloud-fii-data-vishy-bhai-indicator) |
| 24570221 | [BB 2025-11-23](scans/24570221--bb-2025-11-23.md) | Intraday | Volatility | 16 | 1 | [Chartink](https://chartink.com/screener/bb-2025-11-23-2) |
| 24553220 | [Fib retracement](scans/24553220--fib-retracement.md) | Intraday | Price action | 4 | 0 | [Chartink](https://chartink.com/screener/fib-retracement-714) |
| 24534645 | [CCI bullish Territory](scans/24534645--cci-bullish-territory.md) | Intraday | Oscillator | 2 | 0 | [Chartink](https://chartink.com/screener/cci-bullish-territory) |
| 24508146 | [Virgin Pivot on Upside](scans/24508146--virgin-pivot-on-upside.md) | Swing | Support/resistance | 9 | 0 | [Chartink](https://chartink.com/screener/virgin-pivot-on-upside) |
| 24507997 | [Virgin Pivot on Downside](scans/24507997--virgin-pivot-on-downside.md) | Swing | Support/resistance | 9 | 0 | [Chartink](https://chartink.com/screener/virgin-pivot-9) |
| 24504096 | [Fresh Impulse Alerter](scans/24504096--fresh-impulse-alerter.md) | Intraday | Breakout | 5 | 1 | [Chartink](https://chartink.com/screener/fresh-impulse-alerter) |
| 24462563 | [Trade book](scans/24462563--trade-book.md) | Intraday | Moving average | 1 | 2 | [Chartink](https://chartink.com/screener/trade-book-25) |
| 24444695 | [running vwap](scans/24444695--running-vwap.md) | Multi-horizon | Volume/delivery | 6 | 5 | [Chartink](https://chartink.com/screener/running-vwap-2) |
| 24440434 | [Test 2025-11-10](scans/24440434--test-2025-11-10.md) | Intraday | Oscillator | 34 | 3 | [Chartink](https://chartink.com/screener/test-2025-11-10-25) |
| 24439670 | [MACD constraction](scans/24439670--macd-constraction.md) | Intraday | Oscillator | 4 | 2 | [Chartink](https://chartink.com/screener/macd-constraction) |
| 24437051 | [chatgpt candle stories](scans/24437051--chatgpt-candle-stories.md) | Swing | Price action | 16 | 2 | [Chartink](https://chartink.com/screener/chatgpt-candle-stories) |
| 24423971 | [Candle Stories](scans/24423971--candle-stories.md) | Swing | Price action | 48 | 2 | [Chartink](https://chartink.com/screener/halt-candle-7) |
| 24419121 | [MFI OSCILLATION AND EXTREME](scans/24419121--mfi-oscillation-and-extreme.md) | Intraday | Oscillator | 2 | 1 | [Chartink](https://chartink.com/screener/mfi-oscillation-and-extreme) |
| 24394160 | [test liquidity scan](scans/24394160--test-liquidity-scan.md) | Intraday | Oscillator | 16 | 2 | [Chartink](https://chartink.com/screener/test-liquidity-scan) |
| 24392823 | [macd cross after longtime](scans/24392823--macd-cross-after-longtime.md) | Swing | Oscillator | 4 | 0 | [Chartink](https://chartink.com/screener/macd-cross-after-longtime) |
| 24392684 | [Very Near to multi year high](scans/24392684--very-near-to-multi-year-high.md) | Multi-horizon | Breakout | 6 | 0 | [Chartink](https://chartink.com/screener/very-near-to-multi-year-hugh) |
| 24392629 | [Copy - Uptrend stock in a range](scans/24392629--copy---uptrend-stock-in-a-range.md) | Swing | Moving average | 6 | 0 | [Chartink](https://chartink.com/screener/copy-uptrend-stock-in-a-range-83) |
| 24387407 | [Recent Volume Spurt and momentum pickup in fast Stochastic](scans/24387407--recent-volume-spurt-and-momentum-pickup-in-fast-stochastic.md) | Intraday | Oscillator | 3 | 1 | [Chartink](https://chartink.com/screener/recent-volume-spurt-and-momentum-pickup-in-fast-stochastic) |
| 24357149 | [Big gap down..but it is bought..](scans/24357149--big-gap-downbut-it-is-bought.md) | Swing | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/big-gap-down-but-it-is-bought) |
| 24355669 | [Symmetrical Triangle](scans/24355669--symmetrical-triangle.md) | Intraday | Oscillator | 3 | 3 | [Chartink](https://chartink.com/screener/symmetrical-triangle-266) |
| 24347727 | [Breakaway Gap _ BULLISH](scans/24347727--breakaway-gap-_-bullish.md) | Swing | Breakout | 2 | 0 | [Chartink](https://chartink.com/screener/breakaway-gap-bullish-3) |
| 24346362 | [DISTANCE TRAVELLED](scans/24346362--distance-travelled.md) | Swing | Fundamental | 2 | 0 | [Chartink](https://chartink.com/screener/distance-travelled) |
| 24346169 | [RSI DIVERGENCE BEARISH](scans/24346169--rsi-divergence-bearish.md) | Intraday | Oscillator | 8 | 2 | [Chartink](https://chartink.com/screener/rsi-divergence-bearish-137) |
| 24343400 | [RSI DIVERGENCE BULLISH](scans/24343400--rsi-divergence-bullish.md) | Intraday | Oscillator | 8 | 2 | [Chartink](https://chartink.com/screener/rsi-divergence-47474749) |
| 24328605 | [stochastic impulse](scans/24328605--stochastic-impulse.md) | Intraday | Oscillator | 6 | 0 | [Chartink](https://chartink.com/screener/stochastic-impulse) |
| 24291133 | [close and sustain above 21 ema after longtime](scans/24291133--close-and-sustain-above-21-ema-after-longtime.md) | Intraday | Moving average | 4 | 0 | [Chartink](https://chartink.com/screener/close-and-sustain-above-21-ema-after-longtime) |
| 24278623 | [RISING VWAP_MACD](scans/24278623--rising-vwap_macd.md) | Intraday | Oscillator | 1 | 0 | [Chartink](https://chartink.com/screener/rising-vwap-macd) |
| 24275088 | [IB Setup](scans/24275088--ib-setup.md) | Intraday | Moving average | 9 | 0 | [Chartink](https://chartink.com/screener/ib-setup-21) |
| 24266809 | [Bullish FVG 30 min TF](scans/24266809--bullish-fvg-30-min-tf.md) | Intraday | Breakout | 10 | 1 | [Chartink](https://chartink.com/screener/bullish-fvg-30-min-tf) |
| 24264248 | [slow and fast vwap averages](scans/24264248--slow-and-fast-vwap-averages.md) | Intraday | Volume/delivery | 7 | 0 | [Chartink](https://chartink.com/screener/running-vwap) |
| 24233277 | [Bullish FVG Daily TF](scans/24233277--bullish-fvg-daily-tf.md) | Swing | Breakout | 11 | 0 | [Chartink](https://chartink.com/screener/bullish-fvg-daily-tf-7) |
| 24233124 | [Fixed assets increase](scans/24233124--fixed-assets-increase.md) | Positional | Fundamental | 1 | 0 | [Chartink](https://chartink.com/screener/fixed-assets-increase-2) |
| 24213260 | [Volume Interest](scans/24213260--volume-interest.md) | Multi-horizon | Volume/delivery | 6 | 2 | [Chartink](https://chartink.com/screener/volume-interest-5) |
| 24170819 | [gap down below prominent levels](scans/24170819--gap-down-below-prominent-levels.md) | Swing | Breakout | 2 | 0 | [Chartink](https://chartink.com/screener/gap-down-below-prominent-levels) |
| 24136510 | [Gapdown below prev n days low](scans/24136510--gapdown-below-prev-n-days-low.md) | Swing | Breakout | 1 | 0 | [Chartink](https://chartink.com/screener/godown-below-prev-n-days-low) |
| 24124918 | [Ichimoku Breakout hour tf](scans/24124918--ichimoku-breakout-hour-tf.md) | Intraday | Breakout | 20 | 0 | [Chartink](https://chartink.com/screener/ichimoku-breakout-hour-tf) |
| 24124258 | [Ichimoku Breakout](scans/24124258--ichimoku-breakout.md) | Swing | Breakout | 20 | 0 | [Chartink](https://chartink.com/screener/ichimoku-breakout-208) |
| 22648967 | [consolidation week](scans/22648967--consolidation-week.md) | Swing | Other | 1 | 1 | [Chartink](https://chartink.com/screener/consolidation-week-2) |
| 22485435 | [HUGE VOLUME IN LAST 45 MINS](scans/22485435--huge-volume-in-last-45-mins.md) | Intraday | Volume/delivery | 1 | 1 | [Chartink](https://chartink.com/screener/huge-volume-in-last-45-mins) |
| 22479264 | [Near days HIGH at EOD](scans/22479264--near-days-high-at-eod.md) | Intraday | Breakout | 2 | 0 | [Chartink](https://chartink.com/screener/near-days-high-at-eod) |
| 22479205 | [near days LOW at EOD](scans/22479205--near-days-low-at-eod.md) | Intraday | Momentum | 2 | 0 | [Chartink](https://chartink.com/screener/near-days-high-aat-eod) |
| 22277530 | [candle body sum](scans/22277530--candle-body-sum.md) | Intraday | Price action | 2 | 1 | [Chartink](https://chartink.com/screener/candle-body-sum) |
| 22156174 | [MORNING HURRY_EVENING HURRY](scans/22156174--morning-hurry_evening-hurry.md) | Intraday | Volume/delivery | 3 | 3 | [Chartink](https://chartink.com/screener/morning-hurry) |
| 22155375 | [Nimblr's FII-DII Volume Interest Scanner - Proxy_](scans/22155375--nimblrs-fii-dii-volume-interest-scanner---proxy.md) | Swing | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/copy-nimblr-s-fii-dii-volume-interest-scanner-proxy-229) |
| 19471822 | [bull sentiment for long](scans/19471822--bull-sentiment-for-long.md) | Intraday | Other | 1 | 0 | [Chartink](https://chartink.com/screener/bull-sentiment-for-long) |
| 19096857 | [Stocks to add to watchlist](scans/19096857--stocks-to-add-to-watchlist.md) | Positional | Other | 7 | 2 | [Chartink](https://chartink.com/screener/stocks-to-add-to-watchlist) |
| 19081847 | [gap down below monthly low](scans/19081847--gap-down-below-monthly-low.md) | Positional | Breakout | 6 | 0 | [Chartink](https://chartink.com/screener/gap-down-below-monthly-low) |
| 19079244 | [Lightening and its arrest](scans/19079244--lightening-and-its-arrest.md) | Intraday | Volatility | 1 | 2 | [Chartink](https://chartink.com/screener/lightening-and-its-arrest) |
| 19020899 | [price 5% more than kijun](scans/19020899--price-5-more-than-kijun.md) | Swing | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/price-5-more-than-kijun) |
| 19011285 | [sell order down but not buy orders](scans/19011285--sell-order-down-but-not-buy-orders.md) | Swing | Support/resistance | 12 | 2 | [Chartink](https://chartink.com/screener/sell-order-down-but-not-buy-orders) |
| 19004935 | [whole day buy interest...next day gapup or bullish](scans/19004935--whole-day-buy-interestnext-day-gapup-or-bullish.md) | Intraday | Breakout | 1 | 0 | [Chartink](https://chartink.com/screener/whole-day-buy-interest-next-day-gapup-or-bullish) |
| 18988794 | [fib band](scans/18988794--fib-band.md) | Intraday | Price action | 5 | 1 | [Chartink](https://chartink.com/screener/fib-band) |
| 18985037 | [Ichimoku](scans/18985037--ichimoku.md) | Swing | Moving average | 10 | 0 | [Chartink](https://chartink.com/screener/ichimoku-17082169) |
| 18981800 | [Value area shifting upwards](scans/18981800--value-area-shifting-upwards.md) | Intraday | Moving average | 1 | 1 | [Chartink](https://chartink.com/screener/value-area-shifting-upwards) |
| 18980043 | [Gapup Pritham da theory variant 1](scans/18980043--gapup-pritham-da-theory-variant-1.md) | Swing | Breakout | 3 | 1 | [Chartink](https://chartink.com/screener/gapup-pritham-da-theory-variant-1) |
| 18980011 | [Gapup Pritham da theory weekly](scans/18980011--gapup-pritham-da-theory-weekly.md) | Swing | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/gapup-pritham-da-theory-weekly) |
| 18968997 | [Gapup Pritham da theory](scans/18968997--gapup-pritham-da-theory.md) | Swing | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/gapup-pritham-da-theory) |
| 18857175 | [cross prev month low and face buying and close above that low](scans/18857175--cross-prev-month-low-and-face-buying-and-close-above-that-lo.md) | Positional | Other | 3 | 0 | [Chartink](https://chartink.com/screener/cross-prev-month-low-and-face-buying-and-close-above-that-low) |
| 18856987 | [cross prev month high and face selling and close below that high](scans/18856987--cross-prev-month-high-and-face-selling-and-close-below-that.md) | Positional | Other | 3 | 0 | [Chartink](https://chartink.com/screener/cross-prev-month-high-and-face-selling-and-close-below-that-high) |
| 18856034 | [overextension retracement level](scans/18856034--overextension-retracement-level.md) | Positional | Momentum | 3 | 0 | [Chartink](https://chartink.com/screener/overextension-retracement-level) |
| 18761624 | [rsi deep pullback wrt yesterdays RSIs range](scans/18761624--rsi-deep-pullback-wrt-yesterdays-rsis-range.md) | Intraday | Oscillator | 1 | 1 | [Chartink](https://chartink.com/screener/rsi-deep-pullback-wrt-yesterdays-rsis-range) |
| 18614539 | [RSI HIGH NOT BROKEN](scans/18614539--rsi-high-not-broken.md) | Intraday | Oscillator | 1 | 2 | [Chartink](https://chartink.com/screener/rsi-high-not-broken) |
| 18518280 | [acc dist breakout test](scans/18518280--acc-dist-breakout-test.md) | Intraday | Breakout | 1 | 2 | [Chartink](https://chartink.com/screener/acc-dist-breakout-test) |
| 18099671 | [gap down](scans/18099671--gap-down.md) | Swing | Breakout | 1 | 0 | [Chartink](https://chartink.com/screener/gap-down-31074378) |
| 17922024 | [Rsi breakout hourly](scans/17922024--rsi-breakout-hourly.md) | Intraday | Oscillator | 1 | 4 | [Chartink](https://chartink.com/screener/rsi-breakout-hourly-3) |
| 17921581 | [Copy - MINERVINI TTC EMA--NOT SO FAR FROM HOME and with IB by @StocksbyPrakhar](scans/17921581--copy---minervini-ttc-ema--not-so-far-from-home-and-with-ib-b.md) | Swing | Moving average | 19 | 1 | [Chartink](https://chartink.com/screener/copy-minervini-ttc-ema-not-so-far-from-home-and-with-ib-by-atstocksbyprakhar-144) |
| 15854587 | [opposing tails](scans/15854587--opposing-tails.md) | Swing | Other | 2 | 0 | [Chartink](https://chartink.com/screener/opposing-tails) |
| 15840378 | [investment_indicator_gaps](scans/15840378--investment_indicator_gaps.md) | Swing | Breakout | 1 | 0 | [Chartink](https://chartink.com/screener/investment-indicator-gaps) |
| 15839436 | [Radar Watchlist Scan](scans/15839436--radar-watchlist-scan.md) | Intraday | Moving average | 7 | 2 | [Chartink](https://chartink.com/screener/radar-watchlist-scan) |
| 15836493 | [fakeout](scans/15836493--fakeout.md) | Intraday | Price action | 3 | 0 | [Chartink](https://chartink.com/screener/fakeout-231) |
| 15836323 | [big mov and vol in mrng](scans/15836323--big-mov-and-vol-in-mrng.md) | Intraday | Moving average | 2 | 0 | [Chartink](https://chartink.com/screener/big-mov-and-vol-in-mrng) |
| 15811911 | [volume interest](scans/15811911--volume-interest.md) | Intraday | Volume/delivery | 1 | 1 | [Chartink](https://chartink.com/screener/volume-interest-2) |
| 15761742 | [Trade value spurt](scans/15761742--trade-value-spurt.md) | Swing | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/mcap-by-volume) |
| 15190696 | [bstrade ratio](scans/15190696--bstrade-ratio.md) | Intraday | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/bstrade-ratio) |
| 14920923 | [Copy - Madeagledocss](scans/14920923--copy---madeagledocss.md) | Multi-horizon | Oscillator | 15 | 0 | [Chartink](https://chartink.com/screener/copy-madeagledocss-355) |
| 14878932 | [Copy - linear mover with most of the time rising 20ema.](scans/14878932--copy---linear-mover-with-most-of-the-time-rising-20ema.md) | Swing | Moving average | 3 | 0 | [Chartink](https://chartink.com/screener/copy-linear-mover-with-most-of-the-time-rising-20ema) |
| 14641033 | [institution buy smallcap midcap](scans/14641033--institution-buy-smallcap-midcap.md) | Intraday | Moving average | 6 | 3 | [Chartink](https://chartink.com/screener/institution-buy-smallcap-midcap) |
| 14637390 | [institution buy](scans/14637390--institution-buy.md) | Intraday | Volume/delivery | 3 | 5 | [Chartink](https://chartink.com/screener/institution-buy-9) |
| 14544876 | [Marzobhu](scans/14544876--marzobhu.md) | Intraday | Moving average | 3 | 0 | [Chartink](https://chartink.com/screener/marzobhu) |
| 14538398 | [buy accelaration](scans/14538398--buy-accelaration.md) | Intraday | Volume/delivery | 4 | 0 | [Chartink](https://chartink.com/screener/closing-time-buy) |
| 14535670 | [institutional BUY](scans/14535670--institutional-buy.md) | Intraday | Moving average | 3 | 1 | [Chartink](https://chartink.com/screener/institutional-buy-81) |
| 14527084 | [buy orders Daily TF](scans/14527084--buy-orders-daily-tf.md) | Intraday | Fundamental | 6 | 2 | [Chartink](https://chartink.com/screener/buy-orders-daily-tf) |
| 14527035 | [intraday breakout](scans/14527035--intraday-breakout.md) | Intraday | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/intraday-breakout-10637) |
| 14486971 | [big buy order imbalance](scans/14486971--big-buy-order-imbalance.md) | Swing | Volume/delivery | 2 | 0 | [Chartink](https://chartink.com/screener/big-buy-order-imbalance) |
| 14486829 | [gap up succeded after failures](scans/14486829--gap-up-succeded-after-failures.md) | Swing | Breakout | 5 | 0 | [Chartink](https://chartink.com/screener/gap-up-succeded-after-failures) |
| 14482587 | [Trendline breakout](scans/14482587--trendline-breakout.md) | Swing | Breakout | 2 | 0 | [Chartink](https://chartink.com/screener/trendline-breakout-16082161) |
| 14479379 | [Gap up prediction](scans/14479379--gap-up-prediction.md) | Swing | Breakout | 3 | 3 | [Chartink](https://chartink.com/screener/gap-up-prediction-4) |
| 14468705 | [square root black wolf money](scans/14468705--square-root-black-wolf-money.md) | Intraday | Moving average | 1 | 1 | [Chartink](https://chartink.com/screener/square-root-black-wolf-money) |
| 14453432 | [test max breakout](scans/14453432--test-max-breakout.md) | Intraday | Breakout | 7 | 0 | [Chartink](https://chartink.com/screener/test-max-breakout) |
| 14445174 | [hourly initiated trades multiple spike](scans/14445174--hourly-initiated-trades-multiple-spike.md) | Multi-horizon | Fundamental | 9 | 4 | [Chartink](https://chartink.com/screener/hourly-initiated-trades-multiple-spike) |
| 14444980 | [hourly initiated  trades spike](scans/14444980--hourly-initiated-trades-spike.md) | Multi-horizon | Fundamental | 10 | 4 | [Chartink](https://chartink.com/screener/hourly-initiated-trades-spike) |
| 14444866 | [Basic Bull Filter](scans/14444866--basic-bull-filter.md) | Swing | Fundamental | 8 | 4 | [Chartink](https://chartink.com/screener/copy-monster-stocks-by-rohana) |
| 14443121 | [sudden buying interest after 2:30PM](scans/14443121--sudden-buying-interest-after-230pm.md) | Multi-horizon | Fundamental | 18 | 5 | [Chartink](https://chartink.com/screener/sudden-buying-interest-after-2-30pm) |
| 14442966 | [sentiment at EOD wrt morning](scans/14442966--sentiment-at-eod-wrt-morning.md) | Intraday | Moving average | 3 | 0 | [Chartink](https://chartink.com/screener/sentiment-at-eod-wrt-morning) |
| 14439677 | [increasing buyer interest](scans/14439677--increasing-buyer-interest.md) | Intraday | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/increasing-buyer-interest) |
| 14414153 | [Copy - 3 Week Tight Close - OmkarBanne](scans/14414153--copy---3-week-tight-close---omkarbanne.md) | Multi-horizon | Moving average | 5 | 1 | [Chartink](https://chartink.com/screener/copy-3-week-tight-close-omkarbanne-1889) |
| 14370905 | [buying interest at eod.. bullish for tomorrow](scans/14370905--buying-interest-at-eod-bullish-for-tomorrow.md) | Intraday | Moving average | 2 | 5 | [Chartink](https://chartink.com/screener/buying-interest-at-eod-bullish-for-tomorrow) |
| 14364023 | [big bar](scans/14364023--big-bar.md) | Intraday | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/big-bar-37) |
| 14363208 | [Marubozu Bullish 15 mins](scans/14363208--marubozu-bullish-15-mins.md) | Intraday | Moving average | 7 | 0 | [Chartink](https://chartink.com/screener/marubozu-bullish-15-mins) |
| 14363162 | [test bull](scans/14363162--test-bull.md) | Swing | Other | 2 | 0 | [Chartink](https://chartink.com/screener/test-bull-2140) |
| 14361807 | [Kick from close weekly](scans/14361807--kick-from-close-weekly.md) | Swing | Other | 5 | 0 | [Chartink](https://chartink.com/screener/kick-from-close-weekly) |
| 14360641 | [vwma flat; high volume node point](scans/14360641--vwma-flat-high-volume-node-point.md) | Intraday | Moving average | 3 | 0 | [Chartink](https://chartink.com/screener/vwma-flat) |
| 14359879 | [Kick from close](scans/14359879--kick-from-close.md) | Swing | Other | 5 | 0 | [Chartink](https://chartink.com/screener/kick-from-close) |
| 14356179 | [abnormal volume](scans/14356179--abnormal-volume.md) | Intraday | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/abnormal-volume-21) |
| 14325290 | [acc dist cum delta(1 day)_big strength/raise](scans/14325290--acc-dist-cum-delta1-day_big-strengthraise.md) | Intraday | Volume/delivery | 1 | 1 | [Chartink](https://chartink.com/screener/acc-dist-cum-delta-1-day-big-strength-raise) |
| 14324424 | [acc dist big green bar in 1 min TF](scans/14324424--acc-dist-big-green-bar-in-1-min-tf.md) | Intraday | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/acc-dist-big-green-bar-in-1-min-tf) |
| 14324390 | [acc dist breakout](scans/14324390--acc-dist-breakout.md) | Intraday | Breakout | 2 | 0 | [Chartink](https://chartink.com/screener/acc-dist-breakout-3) |
| 14323318 | [acc dist breakout](scans/14323318--acc-dist-breakout.md) | Intraday | Breakout | 2 | 1 | [Chartink](https://chartink.com/screener/acc-dist-breakout-2) |
| 14323191 | [acc dist big green bar](scans/14323191--acc-dist-big-green-bar.md) | Intraday | Moving average | 2 | 0 | [Chartink](https://chartink.com/screener/acc-dist-big-green-bar) |
| 14301087 | [Acc Dist Spike](scans/14301087--acc-dist-spike.md) | Intraday | Volume/delivery | 1 | 1 | [Chartink](https://chartink.com/screener/acc-dist-spike) |
| 14300933 | [Weekly volatility increase](scans/14300933--weekly-volatility-increase.md) | Swing | Volatility | 1 | 0 | [Chartink](https://chartink.com/screener/weekly-volatility-increase) |
| 14289123 | [Price change today](scans/14289123--price-change-today.md) | Swing | Price action | 1 | 0 | [Chartink](https://chartink.com/screener/price-change-today) |
| 14287921 | [Volatility and Liquidity](scans/14287921--volatility-and-liquidity.md) | Intraday | Volatility | 2 | 0 | [Chartink](https://chartink.com/screener/volatility-and-liquidity) |
| 14287355 | [price rejection+ decision point weekly DPs](scans/14287355--price-rejection-decision-point-weekly-dps.md) | Swing | Moving average | 15 | 1 | [Chartink](https://chartink.com/screener/price-rejection-decision-point-weekly-dps) |
| 14285322 | [test 2023-12-20](scans/14285322--test-2023-12-20.md) | Swing | Momentum | 1 | 0 | [Chartink](https://chartink.com/screener/test-2023-12-20-34) |
| 14279880 | [price rejection+ decision point](scans/14279880--price-rejection-decision-point.md) | Intraday | Moving average | 14 | 0 | [Chartink](https://chartink.com/screener/price-rejection-decision-point) |
| 14279802 | [price rejection](scans/14279802--price-rejection.md) | Swing | Other | 2 | 0 | [Chartink](https://chartink.com/screener/price-rejection-624) |
| 14250010 | [rsi blackwolf money movement_PriceAction](scans/14250010--rsi-blackwolf-money-movement_priceaction.md) | Intraday | Oscillator | 1 | 2 | [Chartink](https://chartink.com/screener/rsi-blackwolf-money-movement) |
| 14205599 | [Bulliish reversal?](scans/14205599--bulliish-reversal.md) | Swing | Mean reversion | 2 | 0 | [Chartink](https://chartink.com/screener/bulliish-reversal-2) |
| 14204417 | [Good buys seen](scans/14204417--good-buys-seen.md) | Intraday | Price action | 4 | 2 | [Chartink](https://chartink.com/screener/good-buys-seen) |
| 14194234 | [Huge buyer interest](scans/14194234--huge-buyer-interest.md) | Intraday | Volume/delivery | 1 | 2 | [Chartink](https://chartink.com/screener/huge-buyer-interest) |
| 14177915 | [VOLUME INCREASE IN ALL SESSIONS WRT PREVIOUS DAYS](scans/14177915--volume-increase-in-all-sessions-wrt-previous-days.md) | Intraday | Volume/delivery | 1 | 3 | [Chartink](https://chartink.com/screener/volume-increase-in-all-sessions-wrt-previous-days) |
| 14160188 | [morning hour volume spurt](scans/14160188--morning-hour-volume-spurt.md) | Intraday | Volume/delivery | 1 | 1 | [Chartink](https://chartink.com/screener/morning-hour-volume-spurt) |
| 14151007 | [Copy - Short term breakouts](scans/14151007--copy---short-term-breakouts.md) | Swing | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/copy-short-term-breakouts-28033296) |
| 14147224 | [aggressive bull/bear sentiment](scans/14147224--aggressive-bullbear-sentiment.md) | Intraday | Momentum | 2 | 2 | [Chartink](https://chartink.com/screener/sentiment-56) |
| 14146694 | [market breadth](scans/14146694--market-breadth.md) | Swing | Price action | 1 | 0 | [Chartink](https://chartink.com/screener/market-breadth-273) |
| 14138742 | [last 30mins big money](scans/14138742--last-30mins-big-money.md) | Intraday | Volume/delivery | 1 | 1 | [Chartink](https://chartink.com/screener/last-30mins-big-money) |
| 14138206 | [big traded value in short time](scans/14138206--big-traded-value-in-short-time.md) | Intraday | Momentum | 4 | 0 | [Chartink](https://chartink.com/screener/smart-shock) |
| 14136677 | [mfi spike](scans/14136677--mfi-spike.md) | Intraday | Oscillator | 2 | 3 | [Chartink](https://chartink.com/screener/mfi-spike) |
| 14134754 | [order ratio spike](scans/14134754--order-ratio-spike.md) | Intraday | Volume/delivery | 1 | 9 | [Chartink](https://chartink.com/screener/order-ratio-spike) |
| 14128188 | [cmo fresh strength](scans/14128188--cmo-fresh-strength.md) | Intraday | Price action | 2 | 0 | [Chartink](https://chartink.com/screener/cmo-fresh-strength) |
| 14122969 | [ACC/DIST BIG CHANGE](scans/14122969--accdist-big-change.md) | Intraday | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/acc-dist-big-change) |
| 14122808 | [Accdist daily TF](scans/14122808--accdist-daily-tf.md) | Swing | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/accdist-daily-tf) |
| 14122703 | [stocks those are down even when nifty is up](scans/14122703--stocks-those-are-down-even-when-nifty-is-up.md) | Swing | Price action | 1 | 0 | [Chartink](https://chartink.com/screener/stocks-those-are-down-even-when-nifty-is-up) |
| 14122660 | [stocks those are up even when nifty is down](scans/14122660--stocks-those-are-up-even-when-nifty-is-down.md) | Swing | Price action | 1 | 0 | [Chartink](https://chartink.com/screener/stocks-those-are-up-even-when-nifty-is-down) |
| 14120028 | [accdist](scans/14120028--accdist.md) | Intraday | Volume/delivery | 2 | 0 | [Chartink](https://chartink.com/screener/accdist-75) |
| 14108370 | [order book ratio curve sum](scans/14108370--order-book-ratio-curve-sum.md) | Intraday | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/order-book-ratio-curve-sum) |
| 14108316 | [order book ratio curve shift to upper stages_longterm_6months to year_dailyTF](scans/14108316--order-book-ratio-curve-shift-to-upper-stages_longterm_6month.md) | Swing | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/order-book-ratio-curve-shift-to-upper-stages) |
| 14108251 | [rsi breakout](scans/14108251--rsi-breakout.md) | Swing | Oscillator | 3 | 0 | [Chartink](https://chartink.com/screener/rsi-breakout-871) |
| 14108100 | [order book ratio increasing](scans/14108100--order-book-ratio-increasing.md) | Intraday | Moving average | 2 | 1 | [Chartink](https://chartink.com/screener/order-book-ratio-increasing) |
| 14102444 | [Price change big](scans/14102444--price-change-big.md) | Swing | Price action | 2 | 0 | [Chartink](https://chartink.com/screener/price-change-big) |
| 14086846 | [price near last week's decision points](scans/14086846--price-near-last-weeks-decision-points.md) | Multi-horizon | Other | 9 | 5 | [Chartink](https://chartink.com/screener/price-near-last-week-s-decision-points) |
| 14085524 | [price near psychological level 2](scans/14085524--price-near-psychological-level-2.md) | Intraday | Other | 60 | 0 | [Chartink](https://chartink.com/screener/price-near-psychological-level-2) |
| 14085311 | [price near psychological level](scans/14085311--price-near-psychological-level.md) | Intraday | Other | 60 | 0 | [Chartink](https://chartink.com/screener/price-near-psychological-level) |
| 14084302 | [price near yesterday's decision points](scans/14084302--price-near-yesterdays-decision-points.md) | Intraday | Other | 9 | 0 | [Chartink](https://chartink.com/screener/price-near-yesterday-s-decision-points) |
| 14061466 | [Gap up](scans/14061466--gap-up.md) | Intraday | Breakout | 1 | 1 | [Chartink](https://chartink.com/screener/gap-up-6308) |
| 14046569 | [sudden price change](scans/14046569--sudden-price-change.md) | Intraday | Price action | 2 | 2 | [Chartink](https://chartink.com/screener/sudden-price-change-3) |
| 14009482 | [Retest old low after long time intraday 30min FNO](scans/14009482--retest-old-low-after-long-time-intraday-30min-fno.md) | Intraday | Mean reversion | 4 | 0 | [Chartink](https://chartink.com/screener/retest-old-low-after-long-time-intraday-30min-fno) |
| 14009476 | [Retest old high after long time intraday 30MIN FNO _LESS LOOKBACK_More signals](scans/14009476--retest-old-high-after-long-time-intraday-30min-fno-_less-loo.md) | Intraday | Mean reversion | 3 | 1 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-intraday-30min-fno-less-lookback-more-signals) |
| 14009471 | [Retest old high after long time intraday 30min FNO_More signals](scans/14009471--retest-old-high-after-long-time-intraday-30min-fno_more-sign.md) | Intraday | Mean reversion | 3 | 1 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-intraday-30min-fno-more-signals) |
| 14009154 | [Retest old high after long time intraday 30MIN FNO _LESS LOOKBACK](scans/14009154--retest-old-high-after-long-time-intraday-30min-fno-_less-loo.md) | Intraday | Mean reversion | 4 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-intraday-30min-fno-less-lookback) |
| 14008946 | [Retest old high after long time intraday 30min FNO](scans/14008946--retest-old-high-after-long-time-intraday-30min-fno.md) | Intraday | Mean reversion | 4 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-intraday-30min-fno) |
| 14001530 | [Copy - 3 Week Tight Close - OmkarBanne](scans/14001530--copy---3-week-tight-close---omkarbanne.md) | Multi-horizon | Moving average | 5 | 1 | [Chartink](https://chartink.com/screener/copy-3-week-tight-close-omkarbanne-1596) |
| 13990790 | [Copy - Near All Time High Breakout](scans/13990790--copy---near-all-time-high-breakout.md) | Swing | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/copy-near-all-time-high-breakout-2677) |
| 13971853 | [Fresh All Time Highs](scans/13971853--fresh-all-time-highs.md) | Swing | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/copy-fresh-all-time-highs-2003) |
| 13971015 | [Multi Year Breakout SK](scans/13971015--multi-year-breakout-sk.md) | Positional | Breakout | 6 | 0 | [Chartink](https://chartink.com/screener/multi-year-breakout-sk-51) |
| 13971001 | [52 week breakout](scans/13971001--52-week-breakout.md) | Swing | Breakout | 8 | 0 | [Chartink](https://chartink.com/screener/copy-52-week-breakout-19988) |
| 13970867 | [Intraday more than 20 cr opening candle](scans/13970867--intraday-more-than-20-cr-opening-candle.md) | Intraday | Price action | 1 | 2 | [Chartink](https://chartink.com/screener/copy-intraday-volume-rocker-747) |
| 13966931 | [conitinous good green bars](scans/13966931--conitinous-good-green-bars.md) | Swing | Price action | 3 | 0 | [Chartink](https://chartink.com/screener/conitinous-good-green-bars) |
| 13949916 | [52week high with big base](scans/13949916--52week-high-with-big-base.md) | Swing | Breakout | 2 | 0 | [Chartink](https://chartink.com/screener/52week-high-with-big-base) |
| 13936576 | [continuous big volume](scans/13936576--continuous-big-volume.md) | Swing | Volume/delivery | 4 | 1 | [Chartink](https://chartink.com/screener/continuous-big-volume) |
| 13929589 | [trend change to bull](scans/13929589--trend-change-to-bull.md) | Swing | Moving average | 5 | 0 | [Chartink](https://chartink.com/screener/trend-change-to-bull-2) |
| 13929200 | [big bull push](scans/13929200--big-bull-push.md) | Swing | Moving average | 2 | 0 | [Chartink](https://chartink.com/screener/big-bull-push) |
| 13928984 | [2 or more big green candles in short period](scans/13928984--2-or-more-big-green-candles-in-short-period.md) | Swing | Price action | 4 | 0 | [Chartink](https://chartink.com/screener/2-or-more-big-green-candles-in-short-period) |
| 13928890 | [big volume](scans/13928890--big-volume.md) | Swing | Volume/delivery | 4 | 0 | [Chartink](https://chartink.com/screener/big-volume-5000005) |
| 13928838 | [monthly weekly test](scans/13928838--monthly-weekly-test.md) | Multi-horizon | Price action | 4 | 0 | [Chartink](https://chartink.com/screener/monthly-weekly-test-2) |
| 13928636 | [High Tight Flag](scans/13928636--high-tight-flag.md) | Positional | Price action | 2 | 0 | [Chartink](https://chartink.com/screener/high-tight-flag-23353) |
| 13923666 | [continous gap ups...bullish](scans/13923666--continous-gap-upsbullish.md) | Swing | Breakout | 5 | 0 | [Chartink](https://chartink.com/screener/continous-gap-ups-bullish) |
| 13923572 | [big buy](scans/13923572--big-buy.md) | Swing | Moving average | 4 | 1 | [Chartink](https://chartink.com/screener/big-buy-74) |
| 13922007 | [big buy gap bull](scans/13922007--big-buy-gap-bull.md) | Swing | Breakout | 7 | 0 | [Chartink](https://chartink.com/screener/big-buy-73) |
| 13876894 | [volume spike in last 30 mins](scans/13876894--volume-spike-in-last-30-mins.md) | Intraday | Volume/delivery | 4 | 1 | [Chartink](https://chartink.com/screener/volume-spike-in-last-30-mins) |
| 13876865 | [volume  spike in morning 30 mins](scans/13876865--volume-spike-in-morning-30-mins.md) | Intraday | Volume/delivery | 3 | 1 | [Chartink](https://chartink.com/screener/volume-spike-in-morning-30-mins) |
| 13871896 | [Copy - Highest volume in last 1 year](scans/13871896--copy---highest-volume-in-last-1-year.md) | Swing | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/copy-highest-volume-in-last-1-year-163) |
| 13850263 | [bullish radar_52weeksma](scans/13850263--bullish-radar_52weeksma.md) | Swing | Moving average | 1 | 1 | [Chartink](https://chartink.com/screener/bullish-radar-52weeksma) |
| 13793099 | [Bear 2](scans/13793099--bear-2.md) | Swing | Momentum | 1 | 0 | [Chartink](https://chartink.com/screener/bear-2-141) |
| 13792939 | [Bear](scans/13792939--bear.md) | Swing | Momentum | 2 | 0 | [Chartink](https://chartink.com/screener/bear-102116) |
| 13792059 | [Bull 2023-11-12](scans/13792059--bull-2023-11-12.md) | Swing | Other | 2 | 0 | [Chartink](https://chartink.com/screener/bull-2023-11-12) |
| 13754483 | [trend continuation](scans/13754483--trend-continuation.md) | Swing | Other | 2 | 0 | [Chartink](https://chartink.com/screener/trend-continuation-56) |
| 11726667 | [Copy - SHVCP epic modified](scans/11726667--copy---shvcp-epic-modified.md) | Swing | Fundamental | 11 | 0 | [Chartink](https://chartink.com/screener/copy-shvcp-epic-modified-15) |
| 11702916 | [Keltner channel break continuously](scans/11702916--keltner-channel-break-continuously.md) | Swing | Breakout | 1 | 0 | [Chartink](https://chartink.com/screener/keltner-channel-break-continuously) |
| 11701866 | [Keltner channel break](scans/11701866--keltner-channel-break.md) | Swing | Breakout | 1 | 0 | [Chartink](https://chartink.com/screener/keltner-channel-break) |
| 11701407 | [Darvax Trader Amitabh Jha](scans/11701407--darvax-trader-amitabh-jha.md) | Swing | Fundamental | 5 | 0 | [Chartink](https://chartink.com/screener/darvax-trader-6) |
| 11700493 | [Copy - Just started rising 50ema-- MINERVINI TTC EMA--NOT SO FAR FROM HOME by @StocksbyPrakhar](scans/11700493--copy---just-started-rising-50ema---minervini-ttc-ema--not-so.md) | Swing | Moving average | 15 | 0 | [Chartink](https://chartink.com/screener/copy-just-started-rising-50ema-minervini-ttc-ema-not-so-far-from-home-by-atstocksbyprakhar-61) |
| 11682735 | [Copy - MACD HOOK by @StocksbyPrakhar](scans/11682735--copy---macd-hook-by-stocksbyprakhar.md) | Swing | Oscillator | 11 | 1 | [Chartink](https://chartink.com/screener/copy-macd-hook-by-atstocksbyprakhar-86) |
| 11673677 | [Copy - Linear moving VCP @Stocksbyprakhar](scans/11673677--copy---linear-moving-vcp-stocksbyprakhar.md) | Swing | Fundamental | 15 | 0 | [Chartink](https://chartink.com/screener/copy-linear-moving-vcp-atstocksbyprakhar-157) |
| 11664123 | [Copy - VOLATILITY CONTRACTION WITH ATR AND BB GAP --- @StocksbyPrakhar](scans/11664123--copy---volatility-contraction-with-atr-and-bb-gap-----stocks.md) | Swing | Volatility | 15 | 0 | [Chartink](https://chartink.com/screener/copy-volatility-contraction-with-atr-and-bb-gap-atstocksbyprakhar-108) |
| 11640829 | [test 2023-05-03](scans/11640829--test-2023-05-03.md) | Swing | Other | 4 | 0 | [Chartink](https://chartink.com/screener/test-2023-05-03-8) |
| 11638308 | [SUBASISH PANI trapped buyers](scans/11638308--subasish-pani-trapped-buyers.md) | Swing | Moving average | 5 | 1 | [Chartink](https://chartink.com/screener/subasish-pani-2) |
| 11637186 | [bullish sma](scans/11637186--bullish-sma.md) | Swing | Moving average | 3 | 1 | [Chartink](https://chartink.com/screener/bullish-sma-50100244) |
| 11635844 | [test contraction](scans/11635844--test-contraction.md) | Swing | Volatility | 5 | 8 | [Chartink](https://chartink.com/screener/test-contraction-32) |
| 11635784 | [test Bullish Hammer](scans/11635784--test-bullish-hammer.md) | Swing | Price action | 4 | 1 | [Chartink](https://chartink.com/screener/test-bullish-hammer-2) |
| 11634957 | [test 2023-05-02](scans/11634957--test-2023-05-02.md) | Swing | Moving average | 4 | 5 | [Chartink](https://chartink.com/screener/test-2023-05-02-17) |
| 11634286 | [Marubozu Bullish](scans/11634286--marubozu-bullish.md) | Swing | Moving average | 7 | 0 | [Chartink](https://chartink.com/screener/test-2023-05-02-14) |
| 11634168 | [BASIC FILTER](scans/11634168--basic-filter.md) | Swing | Moving average | 3 | 0 | [Chartink](https://chartink.com/screener/basic-filter-190229) |
| 11620861 | [Copy - Manas Arora momentum scanner](scans/11620861--copy---manas-arora-momentum-scanner.md) | Swing | Moving average | 11 | 0 | [Chartink](https://chartink.com/screener/copy-manas-arora-momentum-scanner-30) |
| 11603968 | [Delivery scan](scans/11603968--delivery-scan.md) | Multi-horizon | Volume/delivery | 1 | 1 | [Chartink](https://chartink.com/screener/delivery-scan-75) |
| 11592434 | [Big opening volume](scans/11592434--big-opening-volume.md) | Intraday | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/big-opening-volume) |
| 11590232 | [big shadow on one side only](scans/11590232--big-shadow-on-one-side-only.md) | Swing | Volatility | 2 | 1 | [Chartink](https://chartink.com/screener/big-shadow-on-one-side-only) |
| 11590167 | [weekly 2023-04-27](scans/11590167--weekly-2023-04-27.md) | Swing | Other | 1 | 0 | [Chartink](https://chartink.com/screener/weekly-2023-04-27) |
| 11589786 | [MORNING 30 MINS BIG RANGE](scans/11589786--morning-30-mins-big-range.md) | Intraday | Volatility | 4 | 0 | [Chartink](https://chartink.com/screener/moring-30-mins-big-range) |
| 11589407 | [big shadow](scans/11589407--big-shadow.md) | Swing | Volatility | 2 | 0 | [Chartink](https://chartink.com/screener/big-wick-15) |
| 11586821 | [gapup beyond previous highs](scans/11586821--gapup-beyond-previous-highs.md) | Swing | Breakout | 3 | 2 | [Chartink](https://chartink.com/screener/gapup-beyond-yesterday-s-high) |
| 11586758 | [continuous gapup sustained](scans/11586758--continuous-gapup-sustained.md) | Swing | Breakout | 2 | 0 | [Chartink](https://chartink.com/screener/continuous-gapup-sustained) |
| 11585071 | [three red bars](scans/11585071--three-red-bars.md) | Swing | Momentum | 9 | 9 | [Chartink](https://chartink.com/screener/three-red-bars-2) |
| 11585052 | [good continuous buying pressure wicks](scans/11585052--good-continuous-buying-pressure-wicks.md) | Swing | Momentum | 2 | 1 | [Chartink](https://chartink.com/screener/good-continuous-buying-preassure-wicks) |
| 11584293 | [good rejection near long term moving average](scans/11584293--good-rejection-near-long-term-moving-average.md) | Swing | Moving average | 12 | 2 | [Chartink](https://chartink.com/screener/good-rejection-near-long-term-moving-average) |
| 11581990 | [sma tight](scans/11581990--sma-tight.md) | Swing | Moving average | 10 | 0 | [Chartink](https://chartink.com/screener/sma-tight-2) |
| 11581030 | [sma crossover](scans/11581030--sma-crossover.md) | Swing | Moving average | 7 | 2 | [Chartink](https://chartink.com/screener/sma-crossover-1157) |
| 11580940 | [Copy - Minervini trend template breadth](scans/11580940--copy---minervini-trend-template-breadth.md) | Swing | Fundamental | 10 | 0 | [Chartink](https://chartink.com/screener/copy-minervini-trend-template-breadth-94) |
| 11577515 | [index entering breakout zone after longtime, with bullish momentum in recent days](scans/11577515--index-entering-breakout-zone-after-longtime-with-bullish-mom.md) | Intraday | Breakout | 4 | 0 | [Chartink](https://chartink.com/screener/index-entering-breakout-zone-after-longtime-with-bullish-momentum-in-recent-days) |
| 11577265 | [entering breakout zone after longtime, with bullish momentum in recent days](scans/11577265--entering-breakout-zone-after-longtime-with-bullish-momentum.md) | Swing | Breakout | 4 | 0 | [Chartink](https://chartink.com/screener/breakout-2023-04-25-7) |
| 11567413 | [Good volume after longtime](scans/11567413--good-volume-after-longtime.md) | Swing | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/good-volume-after-longtime) |
| 11552296 | [Copy - TTC COIL by @Stocksbyprakhar](scans/11552296--copy---ttc-coil-by-stocksbyprakhar.md) | Swing | Fundamental | 18 | 0 | [Chartink](https://chartink.com/screener/copy-ttc-coil-by-atstocksbyprakhar-65) |
| 11552295 | [Copy - Linear moving VCP @Stocksbyprakhar](scans/11552295--copy---linear-moving-vcp-stocksbyprakhar.md) | Swing | Fundamental | 15 | 0 | [Chartink](https://chartink.com/screener/copy-linear-moving-vcp-atstocksbyprakhar-89) |
| 11552294 | [Copy - Linear moving VCP @Stocksbyprakhar](scans/11552294--copy---linear-moving-vcp-stocksbyprakhar.md) | Swing | Fundamental | 15 | 0 | [Chartink](https://chartink.com/screener/copy-linear-moving-vcp-atstocksbyprakhar-88) |
| 11540903 | [good intraday movement stocks](scans/11540903--good-intraday-movement-stocks.md) | Intraday | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/good-intraday-movement-stocks) |
| 11482238 | [Index hunt](scans/11482238--index-hunt.md) | Intraday | Volatility | 1 | 0 | [Chartink](https://chartink.com/screener/index-hunt) |
| 11472894 | [gap up futures](scans/11472894--gap-up-futures.md) | Swing | Breakout | 1 | 0 | [Chartink](https://chartink.com/screener/gap-up-futures-21) |
| 11465892 | [Nifty last hour buy pressure](scans/11465892--nifty-last-hour-buy-pressure.md) | Intraday | Moving average | 1 | 3 | [Chartink](https://chartink.com/screener/nifty-last-hour-buy-pressure) |
| 11465347 | [Last hour volume big](scans/11465347--last-hour-volume-big.md) | Intraday | Volume/delivery | 1 | 3 | [Chartink](https://chartink.com/screener/last-hour-volume-big) |
| 11391333 | [STRONG PRICE REJECTIONS_index_test](scans/11391333--strong-price-rejections_index_test.md) | Intraday | Momentum | 5 | 6 | [Chartink](https://chartink.com/screener/strong-price-rejections-index-test) |
| 11391251 | [STRONG PRICE REJECTIONS_index_BANKNIFTY](scans/11391251--strong-price-rejections_index_banknifty.md) | Swing | Other | 2 | 2 | [Chartink](https://chartink.com/screener/strong-price-rejections-index-banknifty) |
| 11389244 | [STRONG PRICE REJECTIONS_STOCKS](scans/11389244--strong-price-rejections_stocks.md) | Swing | Other | 1 | 1 | [Chartink](https://chartink.com/screener/strong-price-rejections-stocks) |
| 11388421 | [STRONG PRICE REJECTIONS_index](scans/11388421--strong-price-rejections_index.md) | Swing | Other | 2 | 2 | [Chartink](https://chartink.com/screener/test-2023-03-31-11) |
| 11366985 | [twitter_Gapup openbut less than prev high](scans/11366985--twitter_gapup-openbut-less-than-prev-high.md) | Swing | Breakout | 4 | 0 | [Chartink](https://chartink.com/screener/test-2023-03-28-6) |
| 11343359 | [nifty obv](scans/11343359--nifty-obv.md) | Intraday | Volume/delivery | 6 | 11 | [Chartink](https://chartink.com/screener/test-2023-03-24-31) |
| 11341240 | [21D Consolidation BO](scans/11341240--21d-consolidation-bo.md) | Swing | Moving average | 5 | 0 | [Chartink](https://chartink.com/screener/21d-consolidation-bo-4) |
| 11340566 | [TEST 2023-03-24](scans/11340566--test-2023-03-24.md) | Multi-horizon | Moving average | 2 | 9 | [Chartink](https://chartink.com/screener/test-2023-03-24-13) |
| 11340336 | [Breakout + Relative Strength](scans/11340336--breakout-relative-strength.md) | Swing | Breakout | 10 | 0 | [Chartink](https://chartink.com/screener/breakout-relative-strength) |
| 11339593 | [Daily- Stocks which are above ARS & SRS zero line (Laxman rekha)](scans/11339593--daily--stocks-which-are-above-ars-srs-zero-line-laxman-rekha.md) | Swing | Moving average | 8 | 0 | [Chartink](https://chartink.com/screener/daily-relative-strength-stocks-outperforming-the-general-market) |
| 11337092 | [Daily- Relative strength, Stocks outperforming the general market](scans/11337092--daily--relative-strength-stocks-outperforming-the-general-ma.md) | Intraday | Moving average | 13 | 0 | [Chartink](https://chartink.com/screener/test-2023-03-23-24) |
| 11121521 | [UCS_Transaction Value Index_V2](scans/11121521--ucs_transaction-value-index_v2.md) | Intraday | Moving average | 2 | 1 | [Chartink](https://chartink.com/screener/ucs-transaction-value-index-v2) |
| 10766412 | [obv traded_value rsi](scans/10766412--obv-traded_value-rsi.md) | Intraday | Volume/delivery | 13 | 2 | [Chartink](https://chartink.com/screener/obv-traded-value-rsi) |
| 10761810 | [rsi obv divergence test](scans/10761810--rsi-obv-divergence-test.md) | Intraday | Volume/delivery | 5 | 0 | [Chartink](https://chartink.com/screener/rsi-obv-divergence-test) |
| 10755068 | [test Exhaustion](scans/10755068--test-exhaustion.md) | Intraday | Moving average | 2 | 4 | [Chartink](https://chartink.com/screener/test-2023-01-08-28) |
| 10737805 | [trade value___overbought](scans/10737805--trade-value___overbought.md) | Intraday | Mean reversion | 10 | 8 | [Chartink](https://chartink.com/screener/trade-value-overbought) |
| 10727075 | [money bump](scans/10727075--money-bump.md) | Intraday | Moving average | 8 | 4 | [Chartink](https://chartink.com/screener/money-bump) |
| 10715613 | [test time zones](scans/10715613--test-time-zones.md) | Swing | Volume/delivery | 2 | 4 | [Chartink](https://chartink.com/screener/test-time-zones) |
| 10695514 | [test_GANN](scans/10695514--test_gann.md) | Intraday | Volume/delivery | 2 | 5 | [Chartink](https://chartink.com/screener/test-gann-3) |
| 10677085 | [BIG EOD VOL_LESS PRICE MOVE](scans/10677085--big-eod-vol_less-price-move.md) | Intraday | Volume/delivery | 5 | 1 | [Chartink](https://chartink.com/screener/big-eod-vol-less-price-move) |
| 10659431 | [vol buildup and price raise at EOD](scans/10659431--vol-buildup-and-price-raise-at-eod.md) | Intraday | Volume/delivery | 7 | 3 | [Chartink](https://chartink.com/screener/vol-buildup-and-price-raise-at-eod) |
| 10659422 | [vol buildup and price down at EOD](scans/10659422--vol-buildup-and-price-down-at-eod.md) | Intraday | Volume/delivery | 7 | 0 | [Chartink](https://chartink.com/screener/vol-buildup-and-price-down-and-eod) |
| 10658726 | [test 2022-12-29](scans/10658726--test-2022-12-29.md) | Intraday | Volume/delivery | 13 | 1 | [Chartink](https://chartink.com/screener/test-2022-12-29-2) |
| 10508528 | [std dev of DIdiff](scans/10508528--std-dev-of-didiff.md) | Intraday | Volatility | 2 | 2 | [Chartink](https://chartink.com/screener/std-dev-of-didiff) |
| 10387723 | [test 2022-12-01](scans/10387723--test-2022-12-01.md) | Multi-horizon | Oscillator | 8 | 3 | [Chartink](https://chartink.com/screener/test-2022-12-01-37) |
| 10271618 | [test 2022-11-20](scans/10271618--test-2022-11-20.md) | Swing | Volume/delivery | 2 | 0 | [Chartink](https://chartink.com/screener/test-2022-11-20-24) |
| 10271581 | [bullish gap-ups near breakout](scans/10271581--bullish-gap-ups-near-breakout.md) | Swing | Breakout | 4 | 0 | [Chartink](https://chartink.com/screener/bullish-gap-ups-near-breakout) |
| 10271417 | [test 2022-11-20](scans/10271417--test-2022-11-20.md) | Swing | Volume/delivery | 4 | 0 | [Chartink](https://chartink.com/screener/test-2022-11-20-23) |
| 9632080 | [STOCK BIG MOVE](scans/9632080--stock-big-move.md) | Swing | Volume/delivery | 2 | 1 | [Chartink](https://chartink.com/screener/stock-big-move) |
| 9622305 | [Nifty check](scans/9622305--nifty-check.md) | Swing | Other | 1 | 1 | [Chartink](https://chartink.com/screener/nifty-check-16) |
| 9622291 | [Price sum (longterm...for bulk money investment)](scans/9622291--price-sum-longtermfor-bulk-money-investment.md) | Swing | Volume/delivery | 2 | 0 | [Chartink](https://chartink.com/screener/price-sum-longterm-for-bulk-money-investment) |
| 9609082 | [tight intra](scans/9609082--tight-intra.md) | Multi-horizon | Volume/delivery | 6 | 0 | [Chartink](https://chartink.com/screener/tight-intra) |
| 9607841 | ["to observe" list](scans/9607841--to-observe-list.md) | Swing | Moving average | 7 | 1 | [Chartink](https://chartink.com/screener/huge-vol-spike) |
| 9162807 | [overlapping DI+ and DI-](scans/9162807--overlapping-di-and-di.md) | Intraday | Oscillator | 4 | 8 | [Chartink](https://chartink.com/screener/overlapping-di-and-di) |
| 9135205 | [overlapping longterm RSIs](scans/9135205--overlapping-longterm-rsis.md) | Intraday | Oscillator | 8 | 2 | [Chartink](https://chartink.com/screener/overlapping-longterm-rsis) |
| 9124638 | [rsi longterm breakdown](scans/9124638--rsi-longterm-breakdown.md) | Intraday | Oscillator | 13 | 3 | [Chartink](https://chartink.com/screener/rsi-longterm-breakdown) |
| 9107314 | [rsi longterm breakout](scans/9107314--rsi-longterm-breakout.md) | Intraday | Oscillator | 13 | 3 | [Chartink](https://chartink.com/screener/rsi-jump-35) |
| 9023427 | [accdist jump](scans/9023427--accdist-jump.md) | Intraday | Volume/delivery | 9 | 10 | [Chartink](https://chartink.com/screener/accdist-jump) |
| 8957901 | [volume lump knot pack](scans/8957901--volume-lump-knot-pack.md) | Multi-horizon | Volume/delivery | 3 | 4 | [Chartink](https://chartink.com/screener/volume-knot-pack) |
| 8955514 | [Aroon breakdown breakout](scans/8955514--aroon-breakdown-breakout.md) | Intraday | Oscillator | 7 | 0 | [Chartink](https://chartink.com/screener/aroon-breakdown-breakout) |
| 8951771 | [AROON LONG CONSOLIDATION](scans/8951771--aroon-long-consolidation.md) | Intraday | Oscillator | 5 | 0 | [Chartink](https://chartink.com/screener/aroon-long-consolidation) |
| 8951629 | [AROON indicator](scans/8951629--aroon-indicator.md) | Intraday | Oscillator | 7 | 4 | [Chartink](https://chartink.com/screener/aroon-osc-171) |
| 8950111 | [test 2](scans/8950111--test-2.md) | Intraday | Oscillator | 13 | 14 | [Chartink](https://chartink.com/screener/test-2-250221215) |
| 8935670 | [CUM_OF_DIffofDIplusDIminus_Crossover](scans/8935670--cum_of_diffofdiplusdiminus_crossover.md) | Intraday | Oscillator | 2 | 13 | [Chartink](https://chartink.com/screener/test-2022-07-03-22) |
| 8923772 | [acc dist steep change](scans/8923772--acc-dist-steep-change.md) | Multi-horizon | Volume/delivery | 5 | 0 | [Chartink](https://chartink.com/screener/acc-dist-steep-change) |
| 8921630 | [acc dist camarilla second resistance daily](scans/8921630--acc-dist-camarilla-second-resistance-daily.md) | Swing | Support/resistance | 1 | 1 | [Chartink](https://chartink.com/screener/acc-dist-camarilla-second-resistance-daily) |
| 8921443 | [adx second resistance](scans/8921443--adx-second-resistance.md) | Multi-horizon | Oscillator | 1 | 4 | [Chartink](https://chartink.com/screener/adx-second-resistance) |
| 8920714 | [acc dist second support daily](scans/8920714--acc-dist-second-support-daily.md) | Multi-horizon | Support/resistance | 4 | 2 | [Chartink](https://chartink.com/screener/acc-dist-second-support-daily) |
| 8920664 | [acc dist second resistance daily](scans/8920664--acc-dist-second-resistance-daily.md) | Multi-horizon | Support/resistance | 4 | 2 | [Chartink](https://chartink.com/screener/acc-dist-second-resistance-daily) |
| 8895608 | [mfi second resistance 5 min](scans/8895608--mfi-second-resistance-5-min.md) | Intraday | Oscillator | 3 | 4 | [Chartink](https://chartink.com/screener/mfi-second-resistance-5-min) |
| 8871087 | [mfi second resistance](scans/8871087--mfi-second-resistance.md) | Intraday | Oscillator | 3 | 3 | [Chartink](https://chartink.com/screener/mfi-second-resistance) |
| 8854291 | [FIRST RESISTANCE ALL TIMEFRAMES](scans/8854291--first-resistance-all-timeframes.md) | Multi-horizon | Support/resistance | 3 | 1 | [Chartink](https://chartink.com/screener/first-resistance-all-timeframes) |
| 8827276 | [SECOND RESISTANCE ALL TIMEFRAMES](scans/8827276--second-resistance-all-timeframes.md) | Multi-horizon | Support/resistance | 2 | 2 | [Chartink](https://chartink.com/screener/second-resistance-all-timeframes) |
| 8821830 | [SECOND SUPPORT ALL TIMEFRAMES](scans/8821830--second-support-all-timeframes.md) | Multi-horizon | Support/resistance | 3 | 1 | [Chartink](https://chartink.com/screener/second-support-all-timeframes) |
| 8605570 | [vol boost at bottom__bull](scans/8605570--vol-boost-at-bottom__bull.md) | Swing | Moving average | 4 | 3 | [Chartink](https://chartink.com/screener/vol-boost-at-bottom-bull) |
| 8547904 | [fake gap up](scans/8547904--fake-gap-up.md) | Swing | Breakout | 4 | 2 | [Chartink](https://chartink.com/screener/fake-gap-up-1) |
| 8547721 | [fake gap up](scans/8547721--fake-gap-up.md) | Swing | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/fake-gap-up) |
| 8547628 | [fake gapup](scans/8547628--fake-gapup.md) | Intraday | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/fake-gapup) |
| 8520325 | [trade book](scans/8520325--trade-book.md) | Intraday | Fundamental | 7 | 10 | [Chartink](https://chartink.com/screener/trade-book-8) |
| 8425340 | [downdive with noisyvolume](scans/8425340--downdive-with-noisyvolume.md) | Intraday | Volume/delivery | 8 | 2 | [Chartink](https://chartink.com/screener/downdive-with-noisyvolume) |
| 8386169 | [noisy volume for longtime](scans/8386169--noisy-volume-for-longtime.md) | Swing | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/noisy-volume-for-longtime) |
| 8386057 | [Simple Volume with Pocket Pivots](scans/8386057--simple-volume-with-pocket-pivots.md) | Swing | Support/resistance | 9 | 5 | [Chartink](https://chartink.com/screener/simple-volume-with-pocket-pivots-1) |
| 8376486 | [Simple Volume with Pocket Pivots intraday](scans/8376486--simple-volume-with-pocket-pivots-intraday.md) | Intraday | Support/resistance | 7 | 0 | [Chartink](https://chartink.com/screener/simple-volume-with-pocket-pivots-intraday) |
| 8376045 | [Simple Volume with Pocket Pivots](scans/8376045--simple-volume-with-pocket-pivots.md) | Swing | Support/resistance | 8 | 2 | [Chartink](https://chartink.com/screener/simple-volume-with-pocket-pivots) |
| 7790116 | [Heiken Ashi squeeze](scans/7790116--heiken-ashi-squeeze.md) | Swing | Price action | 1 | 0 | [Chartink](https://chartink.com/screener/heiken-ashi-squeeze) |
| 7471995 | [money flow increase](scans/7471995--money-flow-increase.md) | Swing | Fundamental | 8 | 1 | [Chartink](https://chartink.com/screener/money-flow-increase-1) |
| 7470785 | [Big Consecutive Upper Shadows](scans/7470785--big-consecutive-upper-shadows.md) | Swing | Fundamental | 3 | 3 | [Chartink](https://chartink.com/screener/big-consecutive-upper-shadows) |
| 7455141 | [big vol_bigfiercyfightbearsandbulls_endbullswin_BIGBULLfollowsnextday](scans/7455141--big-vol_bigfiercyfightbearsandbulls_endbullswin_bigbullfollo.md) | Swing | Fundamental | 7 | 1 | [Chartink](https://chartink.com/screener/big-vol-bigfiercyfightbearsandbulls-endbullswin-bigbullfollowsnextday) |
| 7443006 | [open low__high jump](scans/7443006--open-low__high-jump.md) | Swing | Fundamental | 5 | 1 | [Chartink](https://chartink.com/screener/open-low-high-jump) |
| 7397158 | [Shakeout of small cap stocks intraday](scans/7397158--shakeout-of-small-cap-stocks-intraday.md) | Intraday | Moving average | 6 | 0 | [Chartink](https://chartink.com/screener/shakeout-of-small-cap-stocks-intraday) |
| 7390198 | [Shakeout with Breakout of Largecap stocks](scans/7390198--shakeout-with-breakout-of-largecap-stocks.md) | Swing | Breakout | 6 | 0 | [Chartink](https://chartink.com/screener/shakeout-with-breakout-of-largecap-stocks) |
| 7390154 | [Shakeout of Large cap stocks](scans/7390154--shakeout-of-large-cap-stocks.md) | Swing | Fundamental | 4 | 0 | [Chartink](https://chartink.com/screener/shakeout-of-large-cap-stocks) |
| 7389960 | [Shakeout with Breakout of small cap stocks](scans/7389960--shakeout-with-breakout-of-small-cap-stocks.md) | Swing | Breakout | 8 | 0 | [Chartink](https://chartink.com/screener/shakeout-with-breakout-of-small-cap-stocks) |
| 7356848 | [Shakeout of small cap stocks](scans/7356848--shakeout-of-small-cap-stocks.md) | Swing | Moving average | 6 | 0 | [Chartink](https://chartink.com/screener/shakeout-of-small-cap-stocks) |
| 7333566 | [cumulative volume _ Accumalation](scans/7333566--cumulative-volume-_-accumalation.md) | Intraday | Volume/delivery | 5 | 0 | [Chartink](https://chartink.com/screener/cumulative-volume-accumalation) |
| 7326685 | [volume boost after price drop](scans/7326685--volume-boost-after-price-drop.md) | Intraday | Volume/delivery | 3 | 1 | [Chartink](https://chartink.com/screener/volume-boost-after-price-drop) |
| 7304743 | [Big GAPUP as Base__Plus Shakeout___BULLISH](scans/7304743--big-gapup-as-base__plus-shakeout___bullish.md) | Swing | Breakout | 2 | 1 | [Chartink](https://chartink.com/screener/big-gapup-as-base-plus-shakeout-bullish) |
| 7266391 | [highs and lows](scans/7266391--highs-and-lows.md) | Swing | Moving average | 1 | 5 | [Chartink](https://chartink.com/screener/highs-and-lows-2) |
| 7233978 | [buy order quantity](scans/7233978--buy-order-quantity.md) | Swing | Moving average | 2 | 1 | [Chartink](https://chartink.com/screener/buy-order-quantity-17) |
| 6420615 | [New 52W Highs at least after 2 months downtrend](scans/6420615--new-52w-highs-at-least-after-2-months-downtrend.md) | Swing | Breakout | 10 | 0 | [Chartink](https://chartink.com/screener/new-52w-highs-at-least-after-2-months-downtrend) |
| 6334594 | [divergence](scans/6334594--divergence.md) | Swing | Oscillator | 2 | 0 | [Chartink](https://chartink.com/screener/divergence-339) |
| 6299032 | [TEST PIVOT](scans/6299032--test-pivot.md) | Multi-horizon | Support/resistance | 2 | 0 | [Chartink](https://chartink.com/screener/test-pivot-38) |
| 6295708 | [my rsi test](scans/6295708--my-rsi-test.md) | Intraday | Oscillator | 1 | 0 | [Chartink](https://chartink.com/screener/my-rsi-test-1) |
| 6183537 | [vol basic](scans/6183537--vol-basic.md) | Intraday | Moving average | 3 | 1 | [Chartink](https://chartink.com/screener/vol-basiic) |
| 6183290 | [tight](scans/6183290--tight.md) | Intraday | Volatility | 3 | 2 | [Chartink](https://chartink.com/screener/tight-2024) |
| 5927031 | [RENKO](scans/5927031--renko.md) | Intraday | Volume/delivery | 3 | 1 | [Chartink](https://chartink.com/screener/renko-50100206) |
| 5427966 | [volume dryup](scans/5427966--volume-dryup.md) | Swing | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/volume-dryup-2) |
| 5382761 | [BULL](scans/5382761--bull.md) | Intraday | Volume/delivery | 2 | 0 | [Chartink](https://chartink.com/screener/bull-210704) |
| 5272812 | [VOLUME BURST 15 MINS TEST](scans/5272812--volume-burst-15-mins-test.md) | Intraday | Volume/delivery | 2 | 6 | [Chartink](https://chartink.com/screener/volume-burst-15-mins-test) |
| 5088812 | [Darvax](scans/5088812--darvax.md) | Swing | Moving average | 1 | 0 | [Chartink](https://chartink.com/screener/darvax-64) |
| 5078042 | [Fall by 10%](scans/5078042--fall-by-10.md) | Swing | Volume/delivery | 2 | 3 | [Chartink](https://chartink.com/screener/fall-by-10) |
| 5062341 | [atr retest low](scans/5062341--atr-retest-low.md) | Intraday | Volatility | 2 | 2 | [Chartink](https://chartink.com/screener/atr-retest-low) |
| 5054497 | [hammer](scans/5054497--hammer.md) | Multi-horizon | Price action | 5 | 0 | [Chartink](https://chartink.com/screener/hammer-16023287) |
| 5030628 | [Momentum Cycles](scans/5030628--momentum-cycles.md) | Swing | Momentum | 1 | 0 | [Chartink](https://chartink.com/screener/momentum-cycles) |
| 5015378 | [long legged Doji](scans/5015378--long-legged-doji.md) | Swing | Price action | 1 | 1 | [Chartink](https://chartink.com/screener/long-legged-doji-18) |
| 5000637 | [close crosses 5 day high](scans/5000637--close-crosses-5-day-high.md) | Multi-horizon | Breakout | 1 | 2 | [Chartink](https://chartink.com/screener/close-crosses-5-day-high) |
| 4981491 | [strength](scans/4981491--strength.md) | Intraday | Momentum | 1 | 1 | [Chartink](https://chartink.com/screener/strength-52) |
| 4934183 | [Retest old low after long time 90%](scans/4934183--retest-old-low-after-long-time-90.md) | Intraday | Mean reversion | 27 | 0 | [Chartink](https://chartink.com/screener/retest-old-low-after-long-time-90) |
| 4933712 | [three black crows](scans/4933712--three-black-crows.md) | Multi-horizon | Other | 12 | 0 | [Chartink](https://chartink.com/screener/three-black-crows-119) |
| 4915531 | [Retest old high after long time ... 90% range](scans/4915531--retest-old-high-after-long-time-90-range.md) | Intraday | Mean reversion | 12 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-90-range) |
| 4910209 | [quick up](scans/4910209--quick-up.md) | Intraday | Other | 9 | 0 | [Chartink](https://chartink.com/screener/quick-up-10) |
| 4909694 | [Bear](scans/4909694--bear.md) | Intraday | Momentum | 6 | 3 | [Chartink](https://chartink.com/screener/bear-30231) |
| 4900291 | [body range breakout](scans/4900291--body-range-breakout.md) | Swing | Breakout | 1 | 0 | [Chartink](https://chartink.com/screener/body-range-breakout) |
| 4880178 | [EOM SCAN](scans/4880178--eom-scan.md) | Intraday | Moving average | 4 | 0 | [Chartink](https://chartink.com/screener/eom-scan) |
| 4870241 | [trade book](scans/4870241--trade-book.md) | Intraday | Moving average | 5 | 14 | [Chartink](https://chartink.com/screener/trade-book-4) |
| 4842804 | [adx breaking channel](scans/4842804--adx-breaking-channel.md) | Intraday | Oscillator | 2 | 2 | [Chartink](https://chartink.com/screener/adx-breaking-channel) |
| 4840623 | [adx](scans/4840623--adx.md) | Intraday | Oscillator | 1 | 1 | [Chartink](https://chartink.com/screener/adx-1111111548) |
| 4833836 | [Daily Fibonacci 61.8 Retracement With Strength](scans/4833836--daily-fibonacci-618-retracement-with-strength.md) | Intraday | Oscillator | 3 | 0 | [Chartink](https://chartink.com/screener/copy-copy-daily-fibonacci-61-8-retracement-with-strength-300) |
| 4807942 | [cum %price change_or_roc breaking channel](scans/4807942--cum-price-change_or_roc-breaking-channel.md) | Intraday | Breakout | 4 | 0 | [Chartink](https://chartink.com/screener/cum-price-change-or-roc) |
| 4798855 | [darvas new](scans/4798855--darvas-new.md) | Intraday | Oscillator | 6 | 2 | [Chartink](https://chartink.com/screener/darvas-new-2) |
| 4788899 | [Darvas Scan + Takushi + 52weekindex>75](scans/4788899--darvas-scan-takushi-52weekindex75.md) | Multi-horizon | Volume/delivery | 12 | 10 | [Chartink](https://chartink.com/screener/darvas-scan-14) |
| 4781077 | [Copy - Copy - RKB DARVAS BOX by AmitabhJha3](scans/4781077--copy---copy---rkb-darvas-box-by-amitabhjha3.md) | Positional | Oscillator | 4 | 2 | [Chartink](https://chartink.com/screener/copy-copy-rkb-darvas-box-by-amitabhjha3) |
| 4781065 | [Copy - Volume Shockers (stocks with rising volumes) by Amitabhjha3](scans/4781065--copy---volume-shockers-stocks-with-rising-volumes-by-amitabh.md) | Multi-horizon | Volume/delivery | 8 | 0 | [Chartink](https://chartink.com/screener/copy-volume-shockers-stocks-with-rising-volumes-by-amitabhjha3-1) |
| 4781062 | [Copy - Volume Shockers by Darvax Trader AmitabhJha +RSI](scans/4781062--copy---volume-shockers-by-darvax-trader-amitabhjha-rsi.md) | Swing | Oscillator | 9 | 0 | [Chartink](https://chartink.com/screener/copy-volume-shockers-by-darvax-trader-amitabhjha-rsi) |
| 4778794 | [Copy - Bulkowski 3 line strike](scans/4778794--copy---bulkowski-3-line-strike.md) | Swing | Moving average | 6 | 0 | [Chartink](https://chartink.com/screener/copy-bulkowski-3-line-strike-6) |
| 4778600 | [Copy - NTN2 - Bearish Tasuki Line](scans/4778600--copy---ntn2---bearish-tasuki-line.md) | Swing | Momentum | 4 | 0 | [Chartink](https://chartink.com/screener/copy-ntn2-bearish-tasuki-line-1) |
| 4778597 | [Copy - Bearish Tasuki line](scans/4778597--copy---bearish-tasuki-line.md) | Swing | Volume/delivery | 6 | 0 | [Chartink](https://chartink.com/screener/copy-bearish-tasuki-line-2) |
| 4778093 | [Copy - GI Downtrend Reversal Bullish Tasuki](scans/4778093--copy---gi-downtrend-reversal-bullish-tasuki.md) | Swing | Mean reversion | 7 | 1 | [Chartink](https://chartink.com/screener/copy-gi-downtrend-reversal-bullish-tasuki) |
| 4777713 | [Copy - Bullish Tasuki Line](scans/4777713--copy---bullish-tasuki-line.md) | Swing | Volume/delivery | 14 | 2 | [Chartink](https://chartink.com/screener/copy-bullish-tasuki-line-38) |
| 4774932 | [Copy - DarvaX Bullish Tasuki Line](scans/4774932--copy---darvax-bullish-tasuki-line.md) | Swing | Other | 2 | 0 | [Chartink](https://chartink.com/screener/copy-darvax-bullish-tasuki-line-1008) |
| 4774597 | [Darvas top level only](scans/4774597--darvas-top-level-only.md) | Intraday | Momentum | 4 | 0 | [Chartink](https://chartink.com/screener/darvas-top-level-only) |
| 4773099 | [darvax](scans/4773099--darvax.md) | Multi-horizon | Moving average | 10 | 2 | [Chartink](https://chartink.com/screener/darvax-52) |
| 4771788 | [Upper Cirucit Stocks](scans/4771788--upper-cirucit-stocks.md) | Swing | Price action | 1 | 3 | [Chartink](https://chartink.com/screener/upper-cirucit-stocks) |
| 4738564 | [near long time support](scans/4738564--near-long-time-support.md) | Intraday | Support/resistance | 4 | 2 | [Chartink](https://chartink.com/screener/near-long-time-support) |
| 4736320 | [frequency](scans/4736320--frequency.md) | Intraday | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/frequency) |
| 4735194 | [price consolidation within 1%](scans/4735194--price-consolidation-within-1.md) | Swing | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/price-consolidation-within-1) |
| 4734317 | [mean area](scans/4734317--mean-area.md) | Swing | Mean reversion | 3 | 0 | [Chartink](https://chartink.com/screener/mean-area) |
| 4710777 | [Price Change Short term all stocks HULL CROSS ABOVE 0](scans/4710777--price-change-short-term-all-stocks-hull-cross-above-0.md) | Multi-horizon | Momentum | 3 | 1 | [Chartink](https://chartink.com/screener/price-change-short-term-all-stocks-hull-cross-above-0) |
| 4710410 | [Price Change Short term all stocks gap down](scans/4710410--price-change-short-term-all-stocks-gap-down.md) | Multi-horizon | Breakout | 15 | 8 | [Chartink](https://chartink.com/screener/price-change-short-term-all-stocks) |
| 4709797 | [6 Montly volume rise](scans/4709797--6-montly-volume-rise.md) | Multi-horizon | Volume/delivery | 3 | 3 | [Chartink](https://chartink.com/screener/6-montly-volume-rise) |
| 4709034 | [Price Change Short term retest low](scans/4709034--price-change-short-term-retest-low.md) | Multi-horizon | Mean reversion | 1 | 2 | [Chartink](https://chartink.com/screener/price-change-short-term-retest-low) |
| 4704687 | [Price Change Long term](scans/4704687--price-change-long-term.md) | Intraday | Price action | 2 | 1 | [Chartink](https://chartink.com/screener/price-change-long-term) |
| 4704408 | [Price Change Short term](scans/4704408--price-change-short-term.md) | Multi-horizon | Momentum | 2 | 1 | [Chartink](https://chartink.com/screener/price-change-33) |
| 4702106 | [Slope](scans/4702106--slope.md) | Intraday | Volume/delivery | 16 | 0 | [Chartink](https://chartink.com/screener/slope-18) |
| 4698979 | [Copy - Gap Up by 3% with 3x volume.15min](scans/4698979--copy---gap-up-by-3-with-3x-volume15min.md) | Intraday | Volume/delivery | 7 | 4 | [Chartink](https://chartink.com/screener/copy-gap-up-by-3-with-3x-volume-15min) |
| 4685873 | [Retest old high after long time weekly](scans/4685873--retest-old-high-after-long-time-weekly.md) | Swing | Mean reversion | 8 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-weekly) |
| 4676962 | [too many time gapup .... Bullish?](scans/4676962--too-many-time-gapup-bullish.md) | Swing | Breakout | 3 | 0 | [Chartink](https://chartink.com/screener/too-many-time-gapup-bullish) |
| 4676584 | [decrease in spread](scans/4676584--decrease-in-spread.md) | Swing | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/decrease-in-spread) |
| 4676431 | [increase in open continuously](scans/4676431--increase-in-open-continuously.md) | Swing | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/increase-in-open-continuously) |
| 4675974 | [triangle](scans/4675974--triangle.md) | Swing | Price action | 4 | 0 | [Chartink](https://chartink.com/screener/triangle-307) |
| 4675886 | [Volume increase after Volume dryup](scans/4675886--volume-increase-after-volume-dryup.md) | Swing | Volume/delivery | 4 | 0 | [Chartink](https://chartink.com/screener/volume-increase-after-volume-dryup) |
| 4670387 | [test 2021-05-25](scans/4670387--test-2021-05-25.md) | Swing | Volume/delivery | 6 | 0 | [Chartink](https://chartink.com/screener/test-2021-05-25-15) |
| 4668213 | [Retest old high after long time Chaikin Money  Flow 15min](scans/4668213--retest-old-high-after-long-time-chaikin-money-flow-15min.md) | Intraday | Mean reversion | 12 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-chaikin-money-flow-15min) |
| 4668172 | [Retest old high after long time Chaikin Money  Flow](scans/4668172--retest-old-high-after-long-time-chaikin-money-flow.md) | Swing | Mean reversion | 8 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-chaikin-money-flow) |
| 4666577 | [retest low](scans/4666577--retest-low.md) | Swing | Mean reversion | 3 | 0 | [Chartink](https://chartink.com/screener/retest-low) |
| 4664681 | [clvol retest](scans/4664681--clvol-retest.md) | Swing | Mean reversion | 3 | 4 | [Chartink](https://chartink.com/screener/clvol-retest) |
| 4664394 | [Retest old low after long time](scans/4664394--retest-old-low-after-long-time.md) | Intraday | Mean reversion | 12 | 0 | [Chartink](https://chartink.com/screener/retest-old-low-after-long-time) |
| 4663438 | [Sideways after downfall](scans/4663438--sideways-after-downfall.md) | Intraday | Volume/delivery | 28 | 3 | [Chartink](https://chartink.com/screener/sideways-after-downfall) |
| 4654246 | [Retest old high after long time intraday 60min](scans/4654246--retest-old-high-after-long-time-intraday-60min.md) | Intraday | Mean reversion | 4 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-intraday-60min) |
| 4652830 | [Retest old high after long time intraday 30min](scans/4652830--retest-old-high-after-long-time-intraday-30min.md) | Intraday | Mean reversion | 4 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-intraday-30min) |
| 4651203 | [Retest old high after long time intraday 15min](scans/4651203--retest-old-high-after-long-time-intraday-15min.md) | Intraday | Mean reversion | 4 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time-intraday) |
| 4639480 | [Retest old high after long time](scans/4639480--retest-old-high-after-long-time.md) | Swing | Mean reversion | 8 | 0 | [Chartink](https://chartink.com/screener/retest-old-high-after-long-time) |
| 4600191 | [Fall by 4%](scans/4600191--fall-by-4.md) | Swing | Volume/delivery | 3 | 3 | [Chartink](https://chartink.com/screener/del-5143) |
| 4593511 | [VOLUME BURST PRICE CONTRACT](scans/4593511--volume-burst-price-contract.md) | Intraday | Volume/delivery | 4 | 2 | [Chartink](https://chartink.com/screener/volume-burst-price-contract) |
| 4591823 | [VOLUME BURST](scans/4591823--volume-burst.md) | Intraday | Volume/delivery | 2 | 5 | [Chartink](https://chartink.com/screener/volume-burst-172) |
| 4589418 | [TRUE BULK DEAL](scans/4589418--true-bulk-deal.md) | Swing | Moving average | 6 | 1 | [Chartink](https://chartink.com/screener/intra-volume-burst) |
| 4331082 | [STOCKS NEAR SUPPORT](scans/4331082--stocks-near-support.md) | Positional | Support/resistance | 3 | 9 | [Chartink](https://chartink.com/screener/stocks-near-support-9) |
| 4252566 | [TEST 2021-04-01](scans/4252566--test-2021-04-01.md) | Swing | Oscillator | 2 | 5 | [Chartink](https://chartink.com/screener/test-2021-04-01-11) |
| 3946659 | [rsi accdist](scans/3946659--rsi-accdist.md) | Swing | Oscillator | 5 | 3 | [Chartink](https://chartink.com/screener/natural-lan-2) |
| 3929262 | [rsi natural lan](scans/3929262--rsi-natural-lan.md) | Intraday | Oscillator | 2 | 6 | [Chartink](https://chartink.com/screener/rsi-natural-lan) |
| 3929249 | [Natural lan](scans/3929249--natural-lan.md) | Swing | Volume/delivery | 2 | 1 | [Chartink](https://chartink.com/screener/natural-lan) |
| 3904691 | [Fibonacci retracement](scans/3904691--fibonacci-retracement.md) | Positional | Oscillator | 2 | 0 | [Chartink](https://chartink.com/screener/fibonacci-retracement-89) |
| 3904493 | [buy_pivot](scans/3904493--buy_pivot.md) | Positional | Support/resistance | 2 | 12 | [Chartink](https://chartink.com/screener/buy-mfi-cci-rsi-wavetred-obvstrong-trend-vwap) |
| 3901831 | [buy_mfi cci rsi wavetred obvstrong trend](scans/3901831--buy_mfi-cci-rsi-wavetred-obvstrong-trend.md) | Swing | Oscillator | 7 | 1 | [Chartink](https://chartink.com/screener/buy-rsi-strong-trend) |
| 3875683 | [del](scans/3875683--del.md) | Swing | Volume/delivery | 2 | 4 | [Chartink](https://chartink.com/screener/copy-top-shares-for-2020-stocks-to-invest-in-324) |
| 2654724 | [PPO PERCENTAGE PRICE OSCILLATOR](scans/2654724--ppo-percentage-price-oscillator.md) | Swing | Moving average | 2 | 9 | [Chartink](https://chartink.com/screener/ppo-percentage-price-oscillator) |
| 2638928 | [RMO](scans/2638928--rmo.md) | Swing | Moving average | 2 | 2 | [Chartink](https://chartink.com/screener/rmo-1) |
| 2638274 | [Dimbetta Moving Average](scans/2638274--dimbetta-moving-average.md) | Swing | Moving average | 2 | 5 | [Chartink](https://chartink.com/screener/dimbetta-moving-average) |
| 2637420 | [Murrey Math Oscillator continuous near top range](scans/2637420--murrey-math-oscillator-continuous-near-top-range.md) | Swing | Volatility | 6 | 2 | [Chartink](https://chartink.com/screener/murrey-math-oscillator-continuous-near-top-range) |
| 2637187 | [Murrey Math Oscillator continuous near bottom range](scans/2637187--murrey-math-oscillator-continuous-near-bottom-range.md) | Swing | Volatility | 6 | 2 | [Chartink](https://chartink.com/screener/murrey-math-oscillator-pullback) |
| 2637175 | [Murrey Math Oscillator BUY](scans/2637175--murrey-math-oscillator-buy.md) | Swing | Other | 2 | 2 | [Chartink](https://chartink.com/screener/murrey-math-oscillator-buy) |
| 2634434 | [Murrey Math Oscillator SELL](scans/2634434--murrey-math-oscillator-sell.md) | Swing | Other | 2 | 2 | [Chartink](https://chartink.com/screener/murrey-math-oscillator) |
| 2628371 | [pull back(daily) in monthly downtrend](scans/2628371--pull-backdaily-in-monthly-downtrend.md) | Positional | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/pull-back-daily-in-monthly-downtrend) |
| 2628313 | [pull back(daily) in monthly uptrend](scans/2628313--pull-backdaily-in-monthly-uptrend.md) | Positional | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/pull-back-daily-in-monthly-uptrend) |
| 2628197 | [pull back(daily) in weekly uptrend](scans/2628197--pull-backdaily-in-weekly-uptrend.md) | Swing | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/pull-back-daily-in-weekly-uptrend) |
| 2628190 | [pull back(daily) in weekly downtrend](scans/2628190--pull-backdaily-in-weekly-downtrend.md) | Swing | Volume/delivery | 3 | 0 | [Chartink](https://chartink.com/screener/pull-back-daily-in-weekly-downtrend) |
| 2615159 | [rs divergence 3](scans/2615159--rs-divergence-3.md) | Swing | Oscillator | 3 | 5 | [Chartink](https://chartink.com/screener/rs-divergence-3) |
| 2615077 | [rsi divergence 2](scans/2615077--rsi-divergence-2.md) | Swing | Oscillator | 15 | 0 | [Chartink](https://chartink.com/screener/rsi-divergence-2-93) |
| 2612742 | [rsi divergence](scans/2612742--rsi-divergence.md) | Swing | Oscillator | 25 | 0 | [Chartink](https://chartink.com/screener/rsi-divergence-267) |
| 2607534 | [nifty check](scans/2607534--nifty-check.md) | Swing | Oscillator | 2 | 0 | [Chartink](https://chartink.com/screener/nifty-check-1) |
| 2597756 | [multiple MFI](scans/2597756--multiple-mfi.md) | Swing | Oscillator | 6 | 5 | [Chartink](https://chartink.com/screener/multiple-mfi-1) |
| 2594885 | [price volume divergence bullish](scans/2594885--price-volume-divergence-bullish.md) | Swing | Volume/delivery | 3 | 1 | [Chartink](https://chartink.com/screener/price-volume-divergence-bullish) |
| 2594772 | [price volume divergence](scans/2594772--price-volume-divergence.md) | Swing | Volume/delivery | 2 | 1 | [Chartink](https://chartink.com/screener/price-volume-divergence) |
| 2592820 | [COUNT STREAK test2](scans/2592820--count-streak-test2.md) | Swing | Oscillator | 4 | 0 | [Chartink](https://chartink.com/screener/count-streak-test2) |
| 2592714 | [Divergence bearish 5% USING COUNT STREAK](scans/2592714--divergence-bearish-5-using-count-streak.md) | Intraday | Oscillator | 4 | 2 | [Chartink](https://chartink.com/screener/count-streak-test) |
| 2591932 | [SBIN BUY](scans/2591932--sbin-buy.md) | Swing | Oscillator | 4 | 2 | [Chartink](https://chartink.com/screener/sbin-40) |
| 2591776 | [SBIN SELL](scans/2591776--sbin-sell.md) | Swing | Oscillator | 6 | 3 | [Chartink](https://chartink.com/screener/divergence-rsi-16) |
| 2591739 | [divergence bearish 5% rsi+cci+mfi](scans/2591739--divergence-bearish-5-rsiccimfi.md) | Swing | Oscillator | 22 | 7 | [Chartink](https://chartink.com/screener/divergence-bearish-5-rsi-cci) |
| 2591662 | [divergence bearish 5% nonrsi](scans/2591662--divergence-bearish-5-nonrsi.md) | Swing | Oscillator | 12 | 7 | [Chartink](https://chartink.com/screener/divergence-bearish-5-nonrsi) |
| 2589970 | [divergence bullish 5%](scans/2589970--divergence-bullish-5.md) | Swing | Oscillator | 11 | 6 | [Chartink](https://chartink.com/screener/divergence-bullish-5-1) |
| 2589369 | [divergence bearish 5%](scans/2589369--divergence-bearish-5.md) | Swing | Oscillator | 12 | 7 | [Chartink](https://chartink.com/screener/divergence-bearish-5-1) |
| 2588433 | [divergence bearish](scans/2588433--divergence-bearish.md) | Swing | Oscillator | 16 | 2 | [Chartink](https://chartink.com/screener/divergence-bearish-61) |
| 2587611 | [divergence bullish](scans/2587611--divergence-bullish.md) | Swing | Oscillator | 10 | 7 | [Chartink](https://chartink.com/screener/divergence-bullish-7) |
| 2587351 | [divergence_priceriseexhuast](scans/2587351--divergence_priceriseexhuast.md) | Swing | Oscillator | 10 | 8 | [Chartink](https://chartink.com/screener/divergence-priceriseexhuast) |
| 2583314 | [price rise volume exhaust](scans/2583314--price-rise-volume-exhaust.md) | Swing | Volume/delivery | 9 | 4 | [Chartink](https://chartink.com/screener/price-rise-volume-exhaust) |
| 2578186 | [Multiple MFI](scans/2578186--multiple-mfi.md) | Intraday | Oscillator | 2 | 7 | [Chartink](https://chartink.com/screener/multiple-mfi) |
| 2568305 | [Copy - Golden Bounce Master 3.5](scans/2568305--copy---golden-bounce-master-35.md) | Swing | Volume/delivery | 20 | 0 | [Chartink](https://chartink.com/screener/copy-golden-bounce-master-3-5-13) |
| 2565684 | [ST Bearish Major Reversal](scans/2565684--st-bearish-major-reversal.md) | Swing | Mean reversion | 4 | 0 | [Chartink](https://chartink.com/screener/st-bearish-major-reversal) |
| 2564238 | [Copy - Bearish Patterns and Failures](scans/2564238--copy---bearish-patterns-and-failures.md) | Swing | Price action | 25 | 0 | [Chartink](https://chartink.com/screener/copy-bearish-patterns-and-failures-40) |
| 2559005 | [Bulkowski short flag 2 DAILY + Monthly Fibonacci retracement  DEAD CAT 90%](scans/2559005--bulkowski-short-flag-2-daily-monthly-fibonacci-retracement-d.md) | Positional | Oscillator | 6 | 1 | [Chartink](https://chartink.com/screener/weekly-fibonacci-retracement-dead-cat-90) |
| 2558632 | [Monthly Fibonacci retracement  DEAD CAT 90%](scans/2558632--monthly-fibonacci-retracement-dead-cat-90.md) | Positional | Oscillator | 2 | 0 | [Chartink](https://chartink.com/screener/copy-monthly-fibonacci-retracement-dead-cat-76-4) |
| 2552713 | [Bulkowski short flag 2 DAILY](scans/2552713--bulkowski-short-flag-2-daily.md) | Swing | Moving average | 4 | 0 | [Chartink](https://chartink.com/screener/test-bulkowski-short-flag-2-shorter-timeframe-1-hour) |
| 2552696 | [Test Bulkowski short flag 2 SHORTER TIMEFRAME 4 HOUR](scans/2552696--test-bulkowski-short-flag-2-shorter-timeframe-4-hour.md) | Intraday | Moving average | 5 | 0 | [Chartink](https://chartink.com/screener/test-bulkowski-short-flag-2-shorter-timeframe) |
| 1464776 | [Copy - Gap Up by 3% with 3x volume.](scans/1464776--copy---gap-up-by-3-with-3x-volume.md) | Swing | Volume/delivery | 7 | 4 | [Chartink](https://chartink.com/screener/copy-gap-up-by-3-with-3x-volume-1520) |
| 1464592 | [VWAP RESISTANCE -- SELL](scans/1464592--vwap-resistance----sell.md) | Intraday | Support/resistance | 5 | 3 | [Chartink](https://chartink.com/screener/test-2019-11-29-7) |
| 1462470 | [Copy -- Stocks near SUPPORT level - bullish (Parimal Wadiwala) EOD](scans/1462470--copy----stocks-near-support-level---bullish-parimal-wadiwala.md) | Intraday | Support/resistance | 3 | 0 | [Chartink](https://chartink.com/screener/copy-stocks-near-support-level-bullish-parimal-wadiwala-eod) |
| 1462351 | [copy -- Stocks near Resistance level - bullish (Parimal Wadiwala) EOD](scans/1462351--copy----stocks-near-resistance-level---bullish-parimal-wadiw.md) | Intraday | Support/resistance | 3 | 0 | [Chartink](https://chartink.com/screener/stocks-near-resistance-level-bullish-parimal-wadiwala-eod-1) |
| 1462293 | [Stocks near Resistance level - bullish (Parimal Wadiwala) EOD](scans/1462293--stocks-near-resistance-level---bullish-parimal-wadiwala-eod.md) | Intraday | Support/resistance | 3 | 0 | [Chartink](https://chartink.com/screener/copy-stocks-near-resistance-level-bullish-parimal-wadiwala-eod-82) |
| 1458485 | [Bulkowski short flag 2 WEEKLY](scans/1458485--bulkowski-short-flag-2-weekly.md) | Swing | Moving average | 4 | 0 | [Chartink](https://chartink.com/screener/copy-bulkowski-short-flag-2-3) |
| 1458410 | [***ShriKrishna RSI3 Consolidation BO](scans/1458410--shrikrishna-rsi3-consolidation-bo.md) | Swing | Oscillator | 5 | 0 | [Chartink](https://chartink.com/screener/copy-shrikrishna-rsi3-consolidation-bo-25) |
| 1457558 | [Consolidation Scanner](scans/1457558--consolidation-scanner.md) | Swing | Other | 12 | 0 | [Chartink](https://chartink.com/screener/copy-consolidation-scanner-17) |
| 1443876 | [BEST BUY STOCKS FOR INTRADAY](scans/1443876--best-buy-stocks-for-intraday.md) | Multi-horizon | Moving average | 14 | 0 | [Chartink](https://chartink.com/screener/copy-best-buy-stocks-for-intraday-756) |
| 1435261 | [Copy - Narrow Range 7 - NR7](scans/1435261--copy---narrow-range-7---nr7.md) | Swing | Moving average | 9 | 0 | [Chartink](https://chartink.com/screener/copy-narrow-range-7-nr7-717) |
| 1434508 | [Standard deviations <80](scans/1434508--standard-deviations-80.md) | Swing | Volatility | 1 | 0 | [Chartink](https://chartink.com/screener/copy-standard-deviations-3) |
| 1434163 | [Jega's 20D BB Brk-up/down consol chk](scans/1434163--jegas-20d-bb-brk-updown-consol-chk.md) | Swing | Volatility | 4 | 0 | [Chartink](https://chartink.com/screener/copy-jega-s-20d-bb-brk-up-down-consol-chk) |
| 1434124 | [Jega's 52W-H/L](scans/1434124--jegas-52w-hl.md) | Swing | Other | 2 | 0 | [Chartink](https://chartink.com/screener/copy-jega-s-52w-h-l) |
| 1434012 | [Copy - Jega's fav NR7 with HH & HL EOD](scans/1434012--copy---jegas-fav-nr7-with-hh-hl-eod.md) | Intraday | Moving average | 12 | 0 | [Chartink](https://chartink.com/screener/copy-jega-s-fav-nr7-with-hh-hl-eod) |
| 1433976 | [Jega's EOD Scripts for Harmonic Bounce](scans/1433976--jegas-eod-scripts-for-harmonic-bounce.md) | Intraday | Moving average | 7 | 0 | [Chartink](https://chartink.com/screener/copy-jega-s-eod-scripts-for-harmonic-bounce-5) |
| 1433924 | [Jega's EOD Scripts for Harmonic Reversals](scans/1433924--jegas-eod-scripts-for-harmonic-reversals.md) | Intraday | Mean reversion | 7 | 0 | [Chartink](https://chartink.com/screener/copy-jega-s-eod-scripts-for-harmonic-reversals-24) |
| 1433848 | [5 Consecutive Dojis EOD Scanner](scans/1433848--5-consecutive-dojis-eod-scanner.md) | Intraday | Price action | 5 | 0 | [Chartink](https://chartink.com/screener/copy-5-consecutive-dojis-eod-scanner-15) |
| 1433762 | [EOD Jackpot -- COMPRESSING CANDLES -- ORIGINAL](scans/1433762--eod-jackpot----compressing-candles----original.md) | Intraday | Price action | 17 | 0 | [Chartink](https://chartink.com/screener/copy-eod-jackpot-49) |
| 1433756 | [EOD Jackpot -- COMPRESSING CANDLES -- PART OF ORIGINAL](scans/1433756--eod-jackpot----compressing-candles----part-of-original.md) | Intraday | Price action | 7 | 0 | [Chartink](https://chartink.com/screener/copy-eod-jackpot-48) |
| 1433731 | [EOD Jackpot -- COMPRESSING CANDLES 2ND](scans/1433731--eod-jackpot----compressing-candles-2nd.md) | Intraday | Price action | 17 | 0 | [Chartink](https://chartink.com/screener/copy-eod-jackpot-47) |
| 1433628 | [EOD Jackpot -- COMPRESSING CANDLES](scans/1433628--eod-jackpot----compressing-candles.md) | Intraday | Price action | 7 | 0 | [Chartink](https://chartink.com/screener/copy-eod-jackpot-46) |
| 1433550 | [VERY far away from vwap -- DAILY -- SHORT](scans/1433550--very-far-away-from-vwap----daily----short.md) | Swing | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/very-far-away-from-vwap-daily-short) |
| 1433456 | [VERY far away from vwap -- DAILY -- LONG](scans/1433456--very-far-away-from-vwap----daily----long.md) | Swing | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/far-away-from-vwap-daily-long) |
| 1433443 | [far away from vwap -- DAILY -- SHORT](scans/1433443--far-away-from-vwap----daily----short.md) | Swing | Volume/delivery | 1 | 0 | [Chartink](https://chartink.com/screener/copy-far-away-from-vwap-1) |
| 1433353 | [COMPRESSED GUPPY WMA](scans/1433353--compressed-guppy-wma.md) | Swing | Moving average | 6 | 0 | [Chartink](https://chartink.com/screener/copy-compressed-guppy-ema-9) |
| 1432131 | [MULTIPLE HULLMA BUNDLING -- HOURLY](scans/1432131--multiple-hullma-bundling----hourly.md) | Intraday | Moving average | 3 | 0 | [Chartink](https://chartink.com/screener/multiple-hullma-bundling-hourly) |
| 1432082 | [MULTIPLE HULL MA BUNDLING](scans/1432082--multiple-hull-ma-bundling.md) | Unspecified | Moving average | 2 | 0 | [Chartink](https://chartink.com/screener/copy-close-above-hull-moving-average-20-70) |
| 1430665 | [TTM squeeze -- NIFTY500](scans/1430665--ttm-squeeze----nifty500.md) | Intraday | Volatility | 10 | 0 | [Chartink](https://chartink.com/screener/copy-ttm-squeeze-95) |
| 1430649 | [TTM squeeze - Daily Chart -- NIFTY500](scans/1430649--ttm-squeeze---daily-chart----nifty500.md) | Swing | Volatility | 10 | 0 | [Chartink](https://chartink.com/screener/copy-ttm-squeeze-daily-chart-13) |
| 1430592 | [Bollinger band Squeeze and NR -- DAILY TIMEFRAME](scans/1430592--bollinger-band-squeeze-and-nr----daily-timeframe.md) | Swing | Volatility | 4 | 0 | [Chartink](https://chartink.com/screener/copy-bollinger-band-squeeze-and-nr-1) |
| 1429703 | [500% - Advance Bollinger Squeeze Scanner -- 4 HOUR TIMEFRAME](scans/1429703--500---advance-bollinger-squeeze-scanner----4-hour-timeframe.md) | Intraday | Volatility | 8 | 0 | [Chartink](https://chartink.com/screener/copy-500-advance-bollinger-squeeze-scanner-15) |
| 1429597 | [bollinger squeeze (++++ l ) -- for 4 hour TIMEFRAME](scans/1429597--bollinger-squeeze-l----for-4-hour-timeframe.md) | Intraday | Volatility | 13 | 0 | [Chartink](https://chartink.com/screener/bollinger-squeeze-l-for-4-hour-timeframe) |

## Classification vocabulary

- Horizon: Intraday, Swing, Positional, Multi-horizon, Unspecified
- Method: Breakout, Trend following, Momentum, Mean reversion, Volume/
  delivery, Price action, Moving average, Oscillator, Volatility,
  Support/resistance, Fundamental, Multi-factor, or Other
- Context tags: long/short bias, market-cap or liquidity universe, index/stock
  universe, and indicator families used

## Page format

Use [the scan template](_template.md) structure. Capture protocol: [_capture-protocol.md](_capture-protocol.md).

QA report: [QA_REPORT.md](QA_REPORT.md)

Generated: 2026-07-15T13:10:16.543992+05:30

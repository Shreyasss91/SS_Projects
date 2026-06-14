import os
import time

from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

api_key = os.getenv("OPENALGO_API_KEY")

client = api(
    api_key=api_key,
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765",
)

instruments = [
    {
        "exchange": "NFO",
        "symbol": "NIFTY16JUN2623400CE:50"
    }
]


def on_data_received(data):

    print("\n" + "=" * 80)

    print("SYMBOL :", data["symbol"])
    print("MODE   :", data["mode"])

    md = data["data"]

    print("LTP    :", md["ltp"])
    print("TIME   :", md["timestamp"])

    bids = md["depth"]["buy"]
    asks = md["depth"]["sell"]

    print("\nLEVELS RECEIVED")
    print("BUY :", len(bids))
    print("SELL:", len(asks))

    best_bid = bids[0]
    best_ask = asks[0]

    print("\nBEST BID")
    print(best_bid)

    print("\nBEST ASK")
    print(best_ask)

    spread = best_ask["price"] - best_bid["price"]

    print("\nSPREAD:", spread)

    total_bid_qty = sum(x["quantity"] for x in bids)
    total_ask_qty = sum(x["quantity"] for x in asks)

    print("\nTOTAL BID QTY:", total_bid_qty)
    print("TOTAL ASK QTY:", total_ask_qty)

    imbalance = (
        (total_bid_qty - total_ask_qty)
        /
        (total_bid_qty + total_ask_qty)
    )

    print("IMBALANCE:", round(imbalance, 4))

    print("=" * 80)


client.connect()

client.subscribe_depth(
    instruments,
    on_data_received=on_data_received
)

try:

    while True:

        time.sleep(5)

        cache = client.get_depth()

        book = (
            cache["depth"]
            ["NFO"]
            ["NIFTY16JUN2623400CE"]
        )

        buy_book = book["buyBook"]
        sell_book = book["sellBook"]

        print("\nCACHE CHECK")
        print("BUY LEVELS :", len(buy_book))
        print("SELL LEVELS:", len(sell_book))

        print("TOP BID:", buy_book["1"])
        print("TOP ASK:", sell_book["1"])

except KeyboardInterrupt:

    client.unsubscribe_depth(instruments)
    client.disconnect()



# this test ouptut
# OpenAlgo Python Bot is running.

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.27
# TIME   : 1781072123

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.1, 'quantity': 520, 'orders': 1}

# BEST ASK
# {'price': 189.45, 'quantity': 650, 'orders': 3}

# SPREAD: 0.3499999999999943

# TOTAL BID QTY: 74165
# TOTAL ASK QTY: 25350
# IMBALANCE: 0.4905
# ================================================================================

# CACHE CHECK
# BUY LEVELS : 50
# SELL LEVELS: 50
# TOP BID: {'price': 189.1, 'qty': 520, 'orders': 1}
# TOP ASK: {'price': 189.45, 'qty': 650, 'orders': 3}

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 188.55
# TIME   : 1781072124

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.5, 'quantity': 130, 'orders': 1}

# BEST ASK
# {'price': 188.6, 'quantity': 130, 'orders': 2}

# SPREAD: 0.09999999999999432

# TOTAL BID QTY: 83395
# TOTAL ASK QTY: 22230
# IMBALANCE: 0.5791
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 188.2
# TIME   : 1781072124

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.0, 'quantity': 1235, 'orders': 10}

# BEST ASK
# {'price': 188.4, 'quantity': 325, 'orders': 2}

# SPREAD: 0.4000000000000057

# TOTAL BID QTY: 69290
# TOTAL ASK QTY: 23465
# IMBALANCE: 0.494
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 188.45
# TIME   : 1781072125

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.25, 'quantity': 455, 'orders': 3}

# BEST ASK
# {'price': 188.65, 'quantity': 260, 'orders': 3}

# SPREAD: 0.4000000000000057

# TOTAL BID QTY: 65520
# TOTAL ASK QTY: 23010
# IMBALANCE: 0.4802
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 188.88
# TIME   : 1781072125

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.65, 'quantity': 455, 'orders': 3}

# BEST ASK
# {'price': 189.1, 'quantity': 325, 'orders': 2}

# SPREAD: 0.44999999999998863

# TOTAL BID QTY: 37960
# TOTAL ASK QTY: 30290
# IMBALANCE: 0.1124
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 188.8
# TIME   : 1781072126

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.6, 'quantity': 260, 'orders': 2}

# BEST ASK
# {'price': 189.0, 'quantity': 195, 'orders': 2}

# SPREAD: 0.4000000000000057

# TOTAL BID QTY: 38220
# TOTAL ASK QTY: 25480
# IMBALANCE: 0.2
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 188.57
# TIME   : 1781072126

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.35, 'quantity': 585, 'orders': 7}

# BEST ASK
# {'price': 188.8, 'quantity': 65, 'orders': 1}

# SPREAD: 0.45000000000001705

# TOTAL BID QTY: 62465
# TOTAL ASK QTY: 23855
# IMBALANCE: 0.4473
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 188.3
# TIME   : 1781072127

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.15, 'quantity': 715, 'orders': 3}

# BEST ASK
# {'price': 188.45, 'quantity': 260, 'orders': 1}

# SPREAD: 0.29999999999998295

# TOTAL BID QTY: 63765
# TOTAL ASK QTY: 22555
# IMBALANCE: 0.4774
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 188.6
# TIME   : 1781072127

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.4, 'quantity': 195, 'orders': 1}

# BEST ASK
# {'price': 188.8, 'quantity': 585, 'orders': 5}

# SPREAD: 0.4000000000000057

# TOTAL BID QTY: 61165
# TOTAL ASK QTY: 21840
# IMBALANCE: 0.4738
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.15
# TIME   : 1781072128

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.95, 'quantity': 650, 'orders': 6}

# BEST ASK
# {'price': 189.35, 'quantity': 65, 'orders': 1}

# SPREAD: 0.4000000000000057

# TOTAL BID QTY: 35945
# TOTAL ASK QTY: 25740
# IMBALANCE: 0.1654
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.7
# TIME   : 1781072128

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.5, 'quantity': 195, 'orders': 1}

# BEST ASK
# {'price': 189.9, 'quantity': 845, 'orders': 7}

# SPREAD: 0.4000000000000057

# TOTAL BID QTY: 37505
# TOTAL ASK QTY: 30290
# IMBALANCE: 0.1064
# ================================================================================

# CACHE CHECK
# BUY LEVELS : 50
# SELL LEVELS: 50
# TOP BID: {'price': 189.5, 'qty': 195, 'orders': 1}
# TOP ASK: {'price': 189.9, 'qty': 845, 'orders': 7}

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.18
# TIME   : 1781072129

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.95, 'quantity': 195, 'orders': 1}

# BEST ASK
# {'price': 189.4, 'quantity': 2080, 'orders': 14}

# SPREAD: 0.45000000000001705

# TOTAL BID QTY: 62920
# TOTAL ASK QTY: 29250
# IMBALANCE: 0.3653
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.32
# TIME   : 1781072129

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.1, 'quantity': 780, 'orders': 4}

# BEST ASK
# {'price': 189.55, 'quantity': 195, 'orders': 3}

# SPREAD: 0.45000000000001705

# TOTAL BID QTY: 36400
# TOTAL ASK QTY: 25740
# IMBALANCE: 0.1715
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.28
# TIME   : 1781072130

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.05, 'quantity': 715, 'orders': 5}

# BEST ASK
# {'price': 189.5, 'quantity': 130, 'orders': 1}

# SPREAD: 0.44999999999998863

# TOTAL BID QTY: 39260
# TOTAL ASK QTY: 24245
# IMBALANCE: 0.2364
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.25
# TIME   : 1781072130

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.05, 'quantity': 65, 'orders': 1}

# BEST ASK
# {'price': 189.45, 'quantity': 715, 'orders': 4}

# SPREAD: 0.39999999999997726

# TOTAL BID QTY: 32955
# TOTAL ASK QTY: 43095
# IMBALANCE: -0.1333
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.15
# TIME   : 1781072131

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.0, 'quantity': 65, 'orders': 1}

# BEST ASK
# {'price': 189.3, 'quantity': 2470, 'orders': 16}

# SPREAD: 0.30000000000001137

# TOTAL BID QTY: 40885
# TOTAL ASK QTY: 43030
# IMBALANCE: -0.0256
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.0
# TIME   : 1781072131

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 188.8, 'quantity': 455, 'orders': 6}

# BEST ASK
# {'price': 189.2, 'quantity': 390, 'orders': 5}

# SPREAD: 0.39999999999997726

# TOTAL BID QTY: 49920
# TOTAL ASK QTY: 34515
# IMBALANCE: 0.1824
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.32
# TIME   : 1781072132

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.1, 'quantity': 195, 'orders': 2}

# BEST ASK
# {'price': 189.55, 'quantity': 845, 'orders': 5}

# SPREAD: 0.45000000000001705

# TOTAL BID QTY: 47060
# TOTAL ASK QTY: 37830
# IMBALANCE: 0.1087
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.32
# TIME   : 1781072132

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.1, 'quantity': 455, 'orders': 5}

# BEST ASK
# {'price': 189.55, 'quantity': 260, 'orders': 2}

# SPREAD: 0.45000000000001705

# TOTAL BID QTY: 36205
# TOTAL ASK QTY: 36335
# IMBALANCE: -0.0018
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.68
# TIME   : 1781072133

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.45, 'quantity': 910, 'orders': 3}

# BEST ASK
# {'price': 189.9, 'quantity': 1430, 'orders': 8}

# SPREAD: 0.45000000000001705

# TOTAL BID QTY: 32045
# TOTAL ASK QTY: 34645
# IMBALANCE: -0.039
# ================================================================================

# CACHE CHECK
# BUY LEVELS : 50
# SELL LEVELS: 50
# TOP BID: {'price': 189.45, 'qty': 910, 'orders': 3}
# TOP ASK: {'price': 189.9, 'qty': 1430, 'orders': 8}

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.7
# TIME   : 1781072133

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.45, 'quantity': 1040, 'orders': 7}

# BEST ASK
# {'price': 189.95, 'quantity': 715, 'orders': 7}

# SPREAD: 0.5

# TOTAL BID QTY: 37570
# TOTAL ASK QTY: 40950
# IMBALANCE: -0.043
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.65
# TIME   : 1781072134

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.4, 'quantity': 1170, 'orders': 8}

# BEST ASK
# {'price': 189.9, 'quantity': 1040, 'orders': 9}

# SPREAD: 0.5

# TOTAL BID QTY: 43485
# TOTAL ASK QTY: 41080
# IMBALANCE: 0.0284
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.62
# TIME   : 1781072134

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.4, 'quantity': 195, 'orders': 2}

# BEST ASK
# {'price': 189.85, 'quantity': 780, 'orders': 3}

# SPREAD: 0.44999999999998863

# TOTAL BID QTY: 55380
# TOTAL ASK QTY: 30615
# IMBALANCE: 0.288
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.53
# TIME   : 1781072135

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.3, 'quantity': 1235, 'orders': 6}

# BEST ASK
# {'price': 189.75, 'quantity': 910, 'orders': 9}

# SPREAD: 0.44999999999998863

# TOTAL BID QTY: 48165
# TOTAL ASK QTY: 43680
# IMBALANCE: 0.0488
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.68
# TIME   : 1781072135

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.45, 'quantity': 520, 'orders': 5}

# BEST ASK
# {'price': 189.9, 'quantity': 1300, 'orders': 8}

# SPREAD: 0.45000000000001705

# TOTAL BID QTY: 33540
# TOTAL ASK QTY: 48880
# IMBALANCE: -0.1861
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.6
# TIME   : 1781072136

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.55, 'quantity': 520, 'orders': 5}

# BEST ASK
# {'price': 189.65, 'quantity': 845, 'orders': 1}

# SPREAD: 0.09999999999999432

# TOTAL BID QTY: 42640
# TOTAL ASK QTY: 34060
# IMBALANCE: 0.1119
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.65
# TIME   : 1781072137

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.45, 'quantity': 130, 'orders': 2}

# BEST ASK
# {'price': 189.85, 'quantity': 520, 'orders': 4}

# SPREAD: 0.4000000000000057

# TOTAL BID QTY: 42900
# TOTAL ASK QTY: 40690
# IMBALANCE: 0.0264
# ================================================================================

# ================================================================================
# SYMBOL : NIFTY16JUN2623400CE:50
# MODE   : 3
# LTP    : 189.57
# TIME   : 1781072138

# LEVELS RECEIVED
# BUY : 50
# SELL: 50

# BEST BID
# {'price': 189.35, 'quantity': 260, 'orders': 3}

# BEST ASK
# {'price': 189.8, 'quantity': 1105, 'orders': 7}

# SPREAD: 0.45000000000001705

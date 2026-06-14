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



# This code's ouptut is below
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
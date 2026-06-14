#!/usr/bin/env python3

import os
import pandas as pd
from openalgo import api

def main():
    print("🔁 OpenAlgo Python Bot is running.")

    api_key = os.getenv("OPENALGO_API_KEY")
    host = os.getenv("HOST_SERVER") or os.getenv("OPENALGO_HOST") or "http://127.0.0.1:5000"


    client = api(api_key=api_key, host=host)
    client = api(
        api_key=api_key,
        host=host
    )

    # UNDERLYING          = "NIFTY"
    # OPTION_EXCHANGE     = "NFO"
    # UNDERLYING_EXCHANGE = "NSE_INDEX"
    # resp = client.expiry(
    #     symbol=UNDERLYING,
    #     exchange=OPTION_EXCHANGE,
    #     instrumenttype="options"
    # )
    # data = resp.get("data")
    # print(data)
    
    
    symbol = "NIFTY16JUN2623200CE"
    exchange = "NFO"

    # 12 June 2026 - 1 minute OHLCV
    df = client.history(
        symbol=symbol,
        exchange=exchange,
        interval="1m",
        start_date="2026-06-11",
        end_date="2026-06-11"
    )

    if df is None or df.empty:
        print("No data returned.")
        return

    required_cols = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        print(f"Missing columns: {missing}")
        return

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    df = df.sort_index()

    print("\n=== DATA SUMMARY ===")
    print(f"Symbol   : {symbol}")
    print(f"Exchange : {exchange}")
    print(f"Rows     : {len(df)}")

    print("\n=== FIRST 5 CANDLES ===")
    print(df.head())

    print("\n=== LAST 5 CANDLES ===")
    print(df.tail())

    # Save locally
    csv_file = f"{symbol}_2026-06-12_1m.csv"
    df.to_csv(csv_file)

    print(f"\nCSV saved: {csv_file}")

if __name__ == "__main__":
    main()
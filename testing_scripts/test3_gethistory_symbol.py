#!/usr/bin/env python3

import os
import pandas as pd
from openalgo import api

# 1. Define the file path inside the logs subfolder
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
# 2. Creates the folder (if not present) before file operations
os.makedirs(logs_dir, exist_ok=True)



def fetch_and_save(client, symbol, exchange, trade_date):
    print(f"\nFetching {symbol}...")

    df = client.history(
        symbol=symbol,
        exchange=exchange,
        interval="1m",
        start_date=trade_date,
        end_date=trade_date
    )

    if df is None or df.empty:
        print(f"No data returned for {symbol}")
        return

    required_cols = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        print(f"{symbol} missing columns: {missing}")
        return

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    df = df.sort_index()

    print(f"Rows: {len(df)}")
    # print(df.head())
    print(df.tail())
    

    csv_file = f"{symbol}_{trade_date}_1m.csv"
    csv_file = os.path.join(logs_dir, f"{symbol}_{trade_date}_1m.csv")
    df.to_csv(csv_file)

    print(f"Saved: {csv_file}")


def main():
    print("🔁 OpenAlgo Python Bot is running.")

    api_key = os.getenv("OPENALGO_API_KEY")
    host = os.getenv("HOST_SERVER") or os.getenv("OPENALGO_HOST") or "http://127.0.0.1:5000"

    client = api(
        api_key=api_key,
        host=host
    )

    instruments = [
        {"symbol": "RELIANCE", "exchange": "NSE"},
        {"symbol": "SBIN", "exchange": "NSE"},
        {"symbol": "TCS", "exchange": "NSE"},
        {"symbol": "NIFTY", "exchange": "NSE_INDEX"},
        {"symbol": "BANKNIFTY", "exchange": "NSE_INDEX"},
        {"symbol": "NIFTY30JUN26FUT", "exchange": "NFO"},
        {"symbol": "NIFTY16JUN2623350CE", "exchange": "NFO"},
        {"symbol": "NIFTY16JUN2623400CE", "exchange": "NFO"},
        {"symbol": "NIFTY16JUN2623600CE", "exchange": "NFO"},
    ]
    trade_date = "2026-06-12"
    

    for inst in instruments:
        fetch_and_save(
            client=client,
            symbol=inst["symbol"],
            exchange=inst["exchange"],
            trade_date=trade_date
        )

if __name__ == "__main__":
    main()
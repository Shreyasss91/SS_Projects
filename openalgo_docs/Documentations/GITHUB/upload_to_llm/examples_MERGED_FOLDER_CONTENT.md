# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\examples\python



---

# FILE: examples\python\backtesting_vectorbt.py

```py
"""
RELIANCE 5-Minute EMA Crossover Backtest using VectorBT
Author : OpenAlgo GPT
Description: Backtests 10/20 EMA crossover strategy on RELIANCE 5m data
             Data fetched from OpenAlgo API, backtested with VectorBT
"""

print("🔁 OpenAlgo Python Bot is running.")

from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import vectorbt as vbt
from openalgo import api, ta
from plotly.subplots import make_subplots

# ───────────────────────── CONFIG ─────────────────────────
API_KEY = "dfae8e3a1ce08f60754b0d3597553d7c14957542104b431e4b881c089864a35e"
API_HOST = "http://127.0.0.1:5000"

SYMBOL = "SBIN"
EXCHANGE = "NSE"
INTERVAL = "15m"

# Date range controls (last 1 year)
END_DATE = datetime.now().strftime("%Y-%m-%d")
START_DATE = (datetime.now() - pd.Timedelta(days=365)).strftime("%Y-%m-%d")

# EMA Parameters
FAST_EMA = 10
SLOW_EMA = 20

# Backtest Parameters
INITIAL_CAPITAL = 100000  # Rs 1,00,000
POSITION_SIZE = 0.5  # 50% of equity
FEES = 0.0011  # 0.11% trading fees

# ─────────────────────── INIT CLIENT ──────────────────────
client = api(api_key=API_KEY, host=API_HOST)


# ───────────────────── FETCH HISTORICAL DATA ─────────────────────
def fetch_historical_data():
    """Fetch 5m historical data for RELIANCE (1 year)"""
    print(f"\nFetching {SYMBOL} {INTERVAL} data from {START_DATE} to {END_DATE}...")
    print("This may take a moment for 1 year of 5m data...")

    response = client.history(
        symbol=SYMBOL,
        exchange=EXCHANGE,
        interval=INTERVAL,
        start_date=START_DATE,
        end_date=END_DATE,
        source = "db"
    )

    # Print the raw response info
    print(f"History Response received: {type(response)}")

    # OpenAlgo history() returns DataFrame directly
    if isinstance(response, pd.DataFrame):
        df = response.copy()
    else:
        df = pd.DataFrame(response.get("data", response))

    if df.empty:
        raise ValueError("No data received from API")

    # Handle index
    if df.index.name == "timestamp" or "timestamp" not in df.columns:
        df.index = pd.to_datetime(df.index)
    else:
        df["datetime"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("datetime")

    df = df.sort_index()
    df.columns = df.columns.str.lower()

    # Ensure timezone-naive for VectorBT compatibility
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    print(f"✅ Fetched {len(df)} candles")
    print(f"📅 Date range: {df.index.min()} to {df.index.max()}")
    print(f"📊 Columns: {list(df.columns)}")

    return df


# ───────────────────── VECTORBT BACKTEST ─────────────────────
def run_backtest(df: pd.DataFrame):
    """Run VectorBT backtest with EMA crossover strategy"""

    print(f"\n{'=' * 60}")
    print("Running EMA Crossover Backtest")
    print(f"Fast EMA: {FAST_EMA} | Slow EMA: {SLOW_EMA}")
    print(f"Initial Capital: ₹{INITIAL_CAPITAL:,}")
    print(f"Position Size: {POSITION_SIZE * 100}% of equity")
    print(f"Fees: {FEES * 100}%")
    print(f"{'=' * 60}\n")

    close = df["close"]

    # Calculate EMAs using VectorBT's built-in MA indicator
    fast_ema = vbt.MA.run(close, FAST_EMA, short_name="fast", ewm=True)
    slow_ema = vbt.MA.run(close, SLOW_EMA, short_name="slow", ewm=True)

    # Generate crossover signals
    entries = fast_ema.ma_crossed_above(slow_ema)
    exits = fast_ema.ma_crossed_below(slow_ema)

    # Print signal counts
    print(f"📈 Total Entry Signals: {entries.sum()}")
    print(f"📉 Total Exit Signals: {exits.sum()}")

    # Create portfolio
    portfolio = vbt.Portfolio.from_signals(
        close,
        entries,
        exits,
        direction="longonly",
        size=POSITION_SIZE,
        size_type="percent",
        fees=FEES,
        init_cash=INITIAL_CAPITAL,
        freq="5min",
        min_size=1,
        size_granularity=1,
    )

    return portfolio, fast_ema, slow_ema, entries, exits


# ───────────────────── PRINT BACKTEST STATS ─────────────────────
def print_backtest_stats(portfolio):
    """Print detailed backtest statistics"""

    stats = portfolio.stats()

    print(f"\n{'=' * 60}")
    print("📊 BACKTEST STATISTICS")
    print(f"{'=' * 60}")
    print(stats)
    print(f"{'=' * 60}\n")

    return stats


# ───────────────────── GET TRADE DETAILS ─────────────────────
def get_trade_details(portfolio):
    """Get and display trade details"""

    trades = portfolio.trades.records_readable

    print(f"\n{'=' * 60}")
    print("📋 TRADE DETAILS")
    print(f"{'=' * 60}")
    print(f"Total Trades: {len(trades)}")
    print("\nFirst 10 Trades:")
    print(trades.head(10).to_string())
    print("\nLast 10 Trades:")
    print(trades.tail(10).to_string())
    print(f"{'=' * 60}\n")

    return trades


# ───────────────────── PLOT RESULTS ─────────────────────
def plot_results(df, portfolio, fast_ema, slow_ema, entries, exits):
    """Create interactive plots for backtest results"""

    # Create x-axis as category strings
    x_category = df.index.strftime("%d-%b-%y<br>%H:%M").tolist()

    # Calculate tick positions
    total_candles = len(x_category)
    tick_step = max(1, total_candles // 20)
    tick_vals = [x_category[i] for i in range(0, total_candles, tick_step)]

    # Get equity and drawdown data
    equity_data = portfolio.value()
    drawdown_data = portfolio.drawdown() * 100

    # Create subplots
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=[
            f"{SYMBOL} Price with EMA({FAST_EMA}/{SLOW_EMA}) Crossover",
            "Equity Curve",
            "Drawdown %",
        ],
    )

    # ───────── ROW 1: Price with EMAs and Signals ─────────

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=x_category,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=SYMBOL,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # Fast EMA
    fig.add_trace(
        go.Scatter(
            x=x_category,
            y=fast_ema.ma.values.flatten(),
            name=f"EMA {FAST_EMA}",
            line=dict(color="blue", width=1),
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # Slow EMA
    fig.add_trace(
        go.Scatter(
            x=x_category,
            y=slow_ema.ma.values.flatten(),
            name=f"EMA {SLOW_EMA}",
            line=dict(color="orange", width=1),
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # Entry signals (Buy) - Fixed indexing
    entry_mask = entries.values.flatten()
    entry_indices = np.where(entry_mask)[0]
    if len(entry_indices) > 0:
        entry_x = [x_category[i] for i in entry_indices if i < len(x_category)]
        entry_y = [df["low"].iloc[i] * 0.995 for i in entry_indices if i < len(df)]

        fig.add_trace(
            go.Scatter(
                x=entry_x,
                y=entry_y,
                mode="markers",
                name="Buy Signal",
                marker=dict(symbol="triangle-up", size=10, color="lime"),
                showlegend=True,
            ),
            row=1,
            col=1,
        )

    # Exit signals (Sell) - Fixed indexing
    exit_mask = exits.values.flatten()
    exit_indices = np.where(exit_mask)[0]
    if len(exit_indices) > 0:
        exit_x = [x_category[i] for i in exit_indices if i < len(x_category)]
        exit_y = [df["high"].iloc[i] * 1.005 for i in exit_indices if i < len(df)]

        fig.add_trace(
            go.Scatter(
                x=exit_x,
                y=exit_y,
                mode="markers",
                name="Sell Signal",
                marker=dict(symbol="triangle-down", size=10, color="red"),
                showlegend=True,
            ),
            row=1,
            col=1,
        )

    # ───────── ROW 2: Equity Curve ─────────
    fig.add_trace(
        go.Scatter(
            x=x_category,
            y=equity_data.values,
            name="Equity",
            line=dict(color="#00bcd4", width=1.5),
            fill="tozeroy",
            fillcolor="rgba(0, 188, 212, 0.1)",
            showlegend=True,
        ),
        row=2,
        col=1,
    )

    # Initial capital line
    fig.add_hline(
        y=INITIAL_CAPITAL,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Initial: ₹{INITIAL_CAPITAL:,}",
        row=2,
        col=1,
    )

    # ───────── ROW 3: Drawdown ─────────
    fig.add_trace(
        go.Scatter(
            x=x_category,
            y=drawdown_data.values,
            name="Drawdown",
            line=dict(color="brown", width=1),
            fill="tozeroy",
            fillcolor="rgba(165, 42, 42, 0.3)",
            showlegend=True,
        ),
        row=3,
        col=1,
    )

    # ───────── LAYOUT ─────────
    fig.update_layout(
        title=dict(
            text=f"{SYMBOL} EMA({FAST_EMA}/{SLOW_EMA}) Crossover Backtest<br>"
            f"<sup>{START_DATE} to {END_DATE} | Initial: ₹{INITIAL_CAPITAL:,} | "
            f"Final: ₹{equity_data.iloc[-1]:,.2f}</sup>",
            x=0.5,
            font=dict(size=16),
        ),
        template="plotly_dark",
        height=1000,
        width=1400,
        hovermode="x unified",
        margin=dict(l=60, r=100, t=100, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Update x-axes
    for row in [1, 2, 3]:
        fig.update_xaxes(
            type="category",
            tickmode="array",
            tickvals=tick_vals,
            tickangle=-45,
            showgrid=True,
            gridcolor="rgba(128, 128, 128, 0.2)",
            rangeslider=dict(visible=False),
            row=row,
            col=1,
        )

    # Update y-axes
    fig.update_yaxes(title="Price (₹)", row=1, col=1)
    fig.update_yaxes(title="Equity (₹)", row=2, col=1)
    fig.update_yaxes(title="Drawdown %", row=3, col=1)

    return fig


# ───────────────────── MAIN EXECUTION ─────────────────────
if __name__ == "__main__":
    try:
        # Step 1: Fetch data from OpenAlgo
        df = fetch_historical_data()

        # Step 2: Run VectorBT backtest
        portfolio, fast_ema, slow_ema, entries, exits = run_backtest(df)

        # Step 3: Print statistics
        stats = print_backtest_stats(portfolio)

        # Step 4: Get trade details
        trades = get_trade_details(portfolio)

        # Step 5: Plot results
        fig = plot_results(df, portfolio, fast_ema, slow_ema, entries, exits)

        # Save as HTML
        output_file = "reliance_ema_backtest.html"
        fig.write_html(output_file)
        print(f"📈 Chart saved to: {output_file}")

        # Show the chart
        fig.show()

        # Also show VectorBT's built-in plot
        print("\n📊 Opening VectorBT Portfolio Plot...")
        portfolio.plot().show()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

```


---

# FILE: examples\python\broker_sdk_downloads.py

```py
"""
Indian broker Python SDK — last-month download stats from PyPI.

Compares the official broker SDKs available on PyPI to give a rough
proxy for community adoption of programmatic-trading clients across
the Indian broker landscape.

Usage:
    pip install pypistats
    python broker_sdk_downloads.py

Notes:
- `pypistats.org` rate-limits to ~1 req/sec per IP; on a cold cache the
  script may need up to a minute total. The retry loop handles HTTP 429
  with widening cooldowns (30s -> 60s -> 90s) so the run does not need
  manual restarts.
- "Last month" is a rolling 30-day window reported by pypistats.org.
- The list is broker-native SDKs (one per broker). OpenAlgo is included
  as the only broker-agnostic abstraction layer in the comparison.
"""

import json
import time

import pypistats

BROKERS = [
    ("Zerodha",      "kiteconnect"),
    ("Angel One",    "smartapi-python"),
    ("Upstox",       "upstox-python-sdk"),
    ("Fyers",        "fyers-apiv3"),
    ("Dhan",         "dhanhq"),
    ("Groww",        "growwapi"),
    ("ICICI Breeze", "breeze-connect"),
    ("5paisa",       "py5paisa"),
    ("OpenAlgo",     "openalgo"),
]


def fetch_last_month(pkg: str, *, max_retries: int = 4, cooldown_sec: int = 30) -> int | None:
    """Return last-month downloads for ``pkg``, retrying on HTTP 429.

    Args:
        pkg: PyPI package name (e.g. "openalgo").
        max_retries: Total attempts before giving up.
        cooldown_sec: Base wait between retries (multiplied by attempt index).

    Returns:
        Last-month download count as int, or None if every attempt fails.
    """
    for attempt in range(max_retries):
        try:
            payload = json.loads(pypistats.recent(pkg, format="json"))
            return int(payload["data"]["last_month"])
        except Exception as exc:
            msg = str(exc)
            if "429" in msg and attempt < max_retries - 1:
                wait = cooldown_sec * (attempt + 1)   # 30s, 60s, 90s
                print(f"  {pkg:25s} rate-limited; cooling down {wait}s...")
                time.sleep(wait)
                continue
            print(f"  {pkg:25s} ERROR after {attempt + 1} attempts: {exc}")
            return None
    return None


def main() -> None:
    results: list[tuple[str, str, int | None]] = []
    for broker, pkg in BROKERS:
        print(f"fetching {broker:15s} ({pkg})...")
        results.append((broker, pkg, fetch_last_month(pkg)))
        time.sleep(2)         # be polite to the pypistats API between calls

    # Sort by downloads descending; missing values pushed to the bottom
    results.sort(key=lambda r: (r[2] is None, -(r[2] or 0)))

    print()
    print(f"{'Rank':>4}  {'Broker':<15} {'PyPI Package':<25} {'Last Month':>12}")
    print(f"{'-' * 4}  {'-' * 15} {'-' * 25} {'-' * 12}")
    for rank, (broker, pkg, downloads) in enumerate(results, 1):
        amount = f"{downloads:,}" if downloads is not None else "n/a"
        marker = "  <-- this project" if pkg == "openalgo" else ""
        print(f"{rank:>4}  {broker:<15} {pkg:<25} {amount:>12}{marker}")


if __name__ == "__main__":
    main()

```


---

# FILE: examples\python\cagr_heatmap.py

```py
# ---------------------------------------------------
# Python Code to Compute Rolling CAGR Heatmap for NIFTY 50
# Recommended to use Daily Historical Data more than 5 Years
# Minor variations in Rolling Returns might occur due to data source differences
# Coded by Rajandran R - Creator of OpenAlgo (https://openalgo.in)
# Author - www.marketcalls.in
# ---------------------------------------------------
# NOTE: This code requires OpenAlgo to be running locally or on a server.
# Get your API key from your self-hosted OpenAlgo platform.
# OpenAlgo GitHub: https://github.com/marketcalls/openalgo
# ---------------------------------------------------

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
from openalgo import api

# ---------------------------------------------------
# Initialize OpenAlgo Client
# ---------------------------------------------------
client = api(api_key="your_api_key_here", host="http://127.0.0.1:5000")

print("🔁 OpenAlgo Python Bot is running.")

# ---------------------------------------------------
# NIFTY 50 SYMBOLS
# ---------------------------------------------------
symbols = [
    "INDIGO",
    "TRENT",
    "HINDUNILVR",
    "HCLTECH",
    "WIPRO",
    "INFY",
    "TATACONSUM",
    "TATASTEEL",
    "ITC",
    "ASIANPAINT",
    "SBILIFE",
    "LT",
    "SHRIRAMFIN",
    "BEL",
    "SBIN",
    "COALINDIA",
    "KOTAKBANK",
    "TCS",
    "SUNPHARMA",
    "MAXHEALTH",
    "NESTLEIND",
    "RELIANCE",
    "ETERNAL",
    "APOLLOHOSP",
    "ICICIBANK",
    "GRASIM",
    "ULTRACEMCO",
    "ADANIENT",
    "AXISBANK",
    "DRREDDY",
    "TECHM",
    "TMPV",
    "JIOFIN",
    "NTPC",
    "BAJFINANCE",
    "BHARTIARTL",
    "POWERGRID",
    "HINDALCO",
    "HDFCBANK",
    "TITAN",
    "HDFCLIFE",
    "MARUTI",
    "BAJAJFINSV",
    "ADANIPORTS",
    "CIPLA",
    "JSWSTEEL",
    "BAJAJ-AUTO",
    "ONGC",
    "EICHERMOT",
    "M&M",
]

TRADING_DAYS_PER_YEAR = 252


# ---------------------------------------------------
# CAGR Calculation (matching TradingView logic)
# ---------------------------------------------------
def calc_cagr(start_price, end_price, years):
    if pd.isna(start_price) or pd.isna(end_price) or start_price <= 0 or end_price <= 0:
        return np.nan
    return ((end_price / start_price) ** (1 / years) - 1) * 100


def get_price_by_trading_days(df, bars_back):
    """Get price exactly N trading bars back (like TradingView)"""
    if len(df) <= bars_back:
        return np.nan
    return df["close"].iloc[-(bars_back + 1)]


# ---------------------------------------------------
# Fetch Historical Data & Calculate CAGRs
# ---------------------------------------------------
results = []

for symbol in symbols:
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 6)  # Extra buffer

        df = client.history(
            symbol=symbol,
            exchange="NSE",
            interval="D",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        if not isinstance(df, pd.DataFrame) or df.empty:
            print(f"{symbol}: No data received")
            results.append([symbol, np.nan, np.nan, np.nan])
            continue

        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        price_now = df["close"].iloc[-1]
        total_bars = len(df)

        if total_bars < TRADING_DAYS_PER_YEAR:
            print(f"{symbol}: Insufficient data ({total_bars} bars)")
            results.append([symbol, np.nan, np.nan, np.nan])
            continue

        # Get prices using trading days (like TradingView)
        bars_1y = TRADING_DAYS_PER_YEAR
        bars_3y = TRADING_DAYS_PER_YEAR * 3
        bars_5y = TRADING_DAYS_PER_YEAR * 5

        price_1y = get_price_by_trading_days(df, bars_1y)
        price_3y = get_price_by_trading_days(df, bars_3y)
        price_5y = get_price_by_trading_days(df, bars_5y)

        # Calculate returns
        abs_1y = ((price_now / price_1y) - 1) * 100 if not pd.isna(price_1y) else np.nan
        cagr_3y = calc_cagr(price_3y, price_now, 3)
        cagr_5y = calc_cagr(price_5y, price_now, 5)

        # Display status
        abs_1y_str = f"{abs_1y:7.2f}%" if not pd.isna(abs_1y) else "N/A"
        cagr_3y_str = f"{cagr_3y:7.2f}%" if not pd.isna(cagr_3y) else "N/A"
        cagr_5y_str = f"{cagr_5y:7.2f}%" if not pd.isna(cagr_5y) else "N/A"
        print(
            f"{symbol:12s} | 1Y: {abs_1y_str:>8s} | 3Y: {cagr_3y_str:>8s} | 5Y: {cagr_5y_str:>8s}"
        )

        results.append([symbol, abs_1y, cagr_3y, cagr_5y])

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        results.append([symbol, np.nan, np.nan, np.nan])

# ---------------------------------------------------
# Create DataFrame
# ---------------------------------------------------
df_cagr = pd.DataFrame(results, columns=["Symbol", "1Y", "3Y", "5Y"])


# ---------------------------------------------------
# Function to Create Heatmap
# ---------------------------------------------------
def create_heatmap(df, period, label):
    df_period = df[["Symbol", period]].copy()

    # Sort by value, putting NaN at the bottom
    df_period = df_period.sort_values(period, ascending=False, na_position="last").reset_index(
        drop=True
    )

    if df_period.empty:
        print(f"⚠️ No data for {label}")
        return

    cols = 10
    df_period["row"] = df_period.index // cols
    df_period["col"] = df_period.index % cols

    # Create display text: "SYMBOL\nValue%" or "SYMBOL\nN/A"
    df_period["display_text"] = df_period.apply(
        lambda row: f"{row['Symbol']}<br>{row[period]:.2f}%"
        if pd.notna(row[period])
        else f"{row['Symbol']}<br>N/A",
        axis=1,
    )

    pivot_values = df_period.pivot(index="row", columns="col", values=period)
    pivot_labels = df_period.pivot(index="row", columns="col", values="display_text")

    fig = px.imshow(pivot_values, color_continuous_scale="RdYlGn", aspect="auto")

    fig.update_traces(
        text=pivot_labels.values, texttemplate="%{text}", hovertemplate="%{text}<extra></extra>"
    )

    fig.update_layout(
        title=f"NIFTY 50 {label} Heatmap (%)",
        xaxis=dict(showticklabels=False, title=""),
        yaxis=dict(showticklabels=False, autorange="reversed", title=""),
        template="plotly_dark",
        height=600,
        width=1200,
    )

    filename = f"nifty50_{period.lower()}_heatmap.png"
    fig.write_image(filename, width=1200, height=600, scale=2)
    print(f"✅ {label} Heatmap saved as {filename}")


# ---------------------------------------------------
# Generate Heatmaps
# ---------------------------------------------------
create_heatmap(df_cagr, "1Y", "1-Year Absolute Return")
create_heatmap(df_cagr, "3Y", "3-Year CAGR")
create_heatmap(df_cagr, "5Y", "5-Year CAGR")

print("\n✅ All heatmaps generated successfully!")

```


---

# FILE: examples\python\data.ipynb

[BINARY FILE]

Type: .ipynb

Size: 11647 bytes

Path: examples\python\data.ipynb


---

# FILE: examples\python\depth_20_example.py

```py
"""
OpenAlgo WebSocket 20-Level Market Depth Example
For brokers that support 20-level depth (Dhan NSE/NFO)
"""

import logging
import time

from openalgo import api

# Configure logging to see WebSocket debug output
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize feed client with explicit parameters
client = api(
    api_key="7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc",  # Replace with your API key
    host="http://127.0.0.1:5000",  # Replace with your API host
    ws_url="ws://127.0.0.1:8765",  # Explicit WebSocket URL (can be different from REST API host)
)

# Instruments for 20-level depth testing
# Use :20 suffix to request 20-level depth (e.g., "TCS:20")
# NFO also supports 20-level depth
instruments_list = [
    {"exchange": "NSE", "symbol": "TCS:20"},
]


def on_data_received(data):
    print("Market Depth Update:")
    print(data)


# Connect and subscribe
client.connect()
client.subscribe_depth(instruments_list, on_data_received=on_data_received)

# Wait a bit for WebSocket to connect and start receiving data
print("\nWaiting for 20-level depth WebSocket to connect and receive data...")
time.sleep(3)

# Poll Market Depth data a few times
for i in range(15):
    print(f"\nPoll {i + 1}:")
    depth = client.get_depth()
    if depth:
        print(depth)
    else:
        print("No depth data yet...")
    time.sleep(1)

# Cleanup
client.unsubscribe_depth(instruments_list)
client.disconnect()

```


---

# FILE: examples\python\depth_50_example.py

```py
"""
OpenAlgo WebSocket 50-Level Market Depth Example
For brokers that support deep market depth (Fyers TBT, etc.)
"""

import logging
import time

from openalgo import api

# Configure logging to see WebSocket debug output
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize feed client with explicit parameters
client = api(
    api_key="7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc",  # Replace with your API key
    host="http://127.0.0.1:5000",  # Replace with your API host
    ws_url="ws://127.0.0.1:8765",  # Explicit WebSocket URL (can be different from REST API host)
)

# Instruments for 50-level depth testing
# Use :50 suffix to request 50-level TBT depth (e.g., "TCS:50")
instruments_list = [{"exchange": "NSE", "symbol": "TCS:50"}]


def on_data_received(data):
    print("Market Depth Update:")
    print(data)


# Connect and subscribe
client.connect()
client.subscribe_depth(instruments_list, on_data_received=on_data_received)

# Wait a bit for WebSocket to connect and start receiving data
print("\nWaiting for TBT WebSocket to connect and receive data...")
time.sleep(3)

# Poll Market Depth data a few times
for i in range(15):
    print(f"\nPoll {i + 1}:")
    depth = client.get_depth()
    if depth:
        print(depth)
    else:
        print("No depth data yet...")
    time.sleep(1)

# Cleanup
client.unsubscribe_depth(instruments_list)
client.disconnect()

```


---

# FILE: examples\python\depth_example.py

```py
"""
OpenAlgo WebSocket Market Depth Example
"""

import time

from openalgo import api

# Initialize feed client with explicit parameters
client = api(
    api_key="7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc",  # Replace with your API key
    host="http://127.0.0.1:5000",  # Replace with your API host
    ws_url="ws://127.0.0.1:8765",  # Explicit WebSocket URL (can be different from REST API host)
)

# MCX instruments for testing
instruments_list = [{"exchange": "NSE", "symbol": "TCS"}]


def on_data_received(data):
    print("Market Depth Update:")
    print(data)


# Connect and subscribe
client.connect()
client.subscribe_depth(instruments_list, on_data_received=on_data_received)

# Poll Market Depth data a few times
for i in range(100):
    print(f"\nPoll {i + 1}:")
    print(client.get_depth())
    time.sleep(0.5)

# Cleanup
client.unsubscribe_depth(instruments_list)
client.disconnect()

```


---

# FILE: examples\python\ema_crossover.py

```py
import threading
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from openalgo import api

# Get API key from openalgo portal
api_key = "your-openalgo-api-key"


# Set the strategy details and trading parameters
strategy = "EMA Crossover Python"
symbol = "BHEL"  # OpenAlgo Symbol
exchange = "NSE"
product = "MIS"
quantity = 1

# EMA periods
fast_period = 5
slow_period = 10

# Set the API Key
client = api(api_key=api_key, host="http://127.0.0.1:5000")


def calculate_ema_signals(df):
    """
    Calculate EMA crossover signals.
    """
    close = df["close"]

    # Calculate EMAs
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()

    # Create crossover signals
    crossover = pd.Series(False, index=df.index)
    crossunder = pd.Series(False, index=df.index)

    # Previous values of EMAs
    prev_fast = ema_fast.shift(1)
    prev_slow = ema_slow.shift(1)

    # Current values of EMAs
    curr_fast = ema_fast
    curr_slow = ema_slow

    # Generate crossover signals
    crossover = (prev_fast < prev_slow) & (curr_fast > curr_slow)
    crossunder = (prev_fast > prev_slow) & (curr_fast < curr_slow)

    return pd.DataFrame(
        {
            "EMA_Fast": ema_fast,
            "EMA_Slow": ema_slow,
            "Crossover": crossover,
            "Crossunder": crossunder,
        },
        index=df.index,
    )


def ema_strategy():
    """
    The EMA crossover trading strategy.
    """
    position = 0

    while True:
        try:
            # Dynamic date range: 7 days back to today
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            # Fetch 1-minute historical data using OpenAlgo
            df = client.history(
                symbol=symbol,
                exchange=exchange,
                interval="1m",
                start_date=start_date,
                end_date=end_date,
            )

            # Check for valid data
            if df.empty:
                print("DataFrame is empty. Retrying...")
                time.sleep(15)
                continue

            # Verify required columns
            if "close" not in df.columns:
                raise KeyError("Missing 'close' column in DataFrame")

            # Round the close column
            df["close"] = df["close"].round(2)

            # Calculate EMAs and signals
            signals = calculate_ema_signals(df)

            # Get latest signals
            crossover = signals["Crossover"].iloc[-2]  # Using -2 to avoid partial candle
            crossunder = signals["Crossunder"].iloc[-2]

            # Execute Buy Order
            if crossover and position <= 0:
                position = quantity
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="BUY",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity,
                    position_size=position,
                )
                print("Buy Order Response:", response)

            # Execute Sell Order
            elif crossunder and position >= 0:
                position = quantity * -1
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="SELL",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity,
                    position_size=position,
                )
                print("Sell Order Response:", response)

            # Log strategy information
            print("\nStrategy Status:")
            print("-" * 50)
            print(f"Position: {position}")
            print(f"LTP: {df['close'].iloc[-1]}")
            print(f"Fast EMA ({fast_period}): {signals['EMA_Fast'].iloc[-2]:.2f}")
            print(f"Slow EMA ({slow_period}): {signals['EMA_Slow'].iloc[-2]:.2f}")
            print(f"Buy Signal: {crossover}")
            print(f"Sell Signal: {crossunder}")
            print("-" * 50)

        except Exception as e:
            print(f"Error in strategy: {str(e)}")
            time.sleep(15)
            continue

        # Wait before the next cycle
        time.sleep(15)


if __name__ == "__main__":
    print(f"Starting {fast_period}/{slow_period} EMA Crossover Strategy...")
    ema_strategy()

```


---

# FILE: examples\python\emacrossover_strategy_python.py

```py
"""
===============================================================================
                EMA CROSSOVER WITH FIXED DATETIME HANDLING
                            OpenAlgo Trading Bot
===============================================================================

Run standalone:
    export OPENALGO_API_KEY="your-api-key"
    python emacrossover_strategy_python.py

Run via OpenAlgo's /python strategy runner:
    OPENALGO_API_KEY            : injected per-strategy (PR #1247).
    OPENALGO_STRATEGY_EXCHANGE  : set from the strategy's `exchange` config
                                  (NSE / BSE / NFO / BFO / MCX / BCD / CDS / CRYPTO).
                                  Drives both this script's trading exchange and
                                  the host's calendar/holiday gating, so the two
                                  always agree (no NSE-only orders on an MCX-gated
                                  strategy).
    STRATEGY_ID / STRATEGY_NAME : injected for log/order tagging.
    HOST_SERVER / WEBSOCKET_URL : inherited from OpenAlgo's .env.
    No code changes required.
"""

import os
import threading
import time
from datetime import datetime, timedelta

import pandas as pd
from openalgo import api

# ===============================================================================
# TRADING CONFIGURATION
# ===============================================================================

# API Configuration — read from environment with sensible fallbacks.
# When launched via OpenAlgo's /python runner, these come from the platform:
#   OPENALGO_API_KEY : injected per-strategy (decrypted from DB)
#   HOST_SERVER      : inherited from OpenAlgo's .env
#   WEBSOCKET_URL    : inherited from OpenAlgo's .env
API_KEY = os.getenv("OPENALGO_API_KEY", "openalgo-apikey")
API_HOST = os.getenv("HOST_SERVER", "http://127.0.0.1:5000")
WS_URL = os.getenv("WEBSOCKET_URL", "ws://127.0.0.1:8765")

# Trade Settings
# EXCHANGE prefers OPENALGO_STRATEGY_EXCHANGE (set by /python runner from the
# strategy's config) so the script trades on whichever exchange the host is
# gating its calendar against. Falls back to EXCHANGE env var, then NSE.
SYMBOL = os.getenv("SYMBOL", "NHPC")              # Stock to trade
EXCHANGE = os.getenv(
    "OPENALGO_STRATEGY_EXCHANGE",
    os.getenv("EXCHANGE", "NSE"),
)                                                 # NSE, BSE, NFO, BFO, MCX, BCD, CDS, CRYPTO
QUANTITY = int(os.getenv("QUANTITY", "1"))        # Number of shares
PRODUCT = os.getenv("PRODUCT", "MIS")             # MIS (Intraday) or CNC (Delivery)

# Strategy Parameters
FAST_EMA_PERIOD = int(os.getenv("FAST_EMA_PERIOD", "2"))
SLOW_EMA_PERIOD = int(os.getenv("SLOW_EMA_PERIOD", "4"))
CANDLE_TIMEFRAME = os.getenv("CANDLE_TIMEFRAME", "5m")  # 1m, 5m, 15m, 30m, 1h, 1d

# Historical Data Lookback (1-30 days)
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "3"))

# Risk Management (Rupees)
STOPLOSS = float(os.getenv("STOPLOSS", "0.1"))
TARGET = float(os.getenv("TARGET", "0.2"))

# Direction Control: LONG, SHORT, BOTH
TRADE_DIRECTION = os.getenv("TRADE_DIRECTION", "BOTH")

# Signal Check Interval (seconds)
SIGNAL_CHECK_INTERVAL = int(os.getenv("SIGNAL_CHECK_INTERVAL", "5"))

# ===============================================================================
# TRADING BOT WITH FIXED DATETIME
# ===============================================================================


class ConfigurableEMABot:
    def __init__(self):
        """Initialize the trading bot with configurable parameters"""
        # Initialize API client
        self.client = api(
            api_key=API_KEY,
            host=API_HOST,
            ws_url=WS_URL,
        )

        # Position tracking
        self.position = None
        self.entry_price = 0
        self.stoploss_price = 0
        self.target_price = 0

        # Real-time price tracking
        self.ltp = None
        self.exit_in_progress = False

        # Thread control
        self.running = True
        self.stop_event = threading.Event()

        # Instrument for WebSocket
        self.instrument = [{"exchange": EXCHANGE, "symbol": SYMBOL}]

        # Strategy name — honor STRATEGY_NAME from the platform if present.
        self.strategy_name = os.getenv("STRATEGY_NAME", f"EMA_{TRADE_DIRECTION}")

        # Validate lookback period
        if LOOKBACK_DAYS < 1:
            print("[WARNING] LOOKBACK_DAYS too small, setting to 1")
            self.lookback_days = 1
        elif LOOKBACK_DAYS > 30:
            print("[WARNING] LOOKBACK_DAYS too large, setting to 30")
            self.lookback_days = 30
        else:
            self.lookback_days = LOOKBACK_DAYS

        print("[BOT] OpenAlgo Trading Bot Started")
        print(f"[BOT] Host: {API_HOST} | WS: {WS_URL}")
        print(f"[BOT] Symbol: {SYMBOL} on {EXCHANGE}")
        print(f"[BOT] Direction Mode: {TRADE_DIRECTION}")
        print(f"[BOT] Strategy: {FAST_EMA_PERIOD} EMA x {SLOW_EMA_PERIOD} EMA")
        print(f"[BOT] Lookback Period: {self.lookback_days} days")
        print(f"[BOT] Signal Check Interval: {SIGNAL_CHECK_INTERVAL} seconds")
        if os.getenv("OPENALGO_STRATEGY_EXCHANGE"):
            print(
                f"[BOT] Exchange resolved from OPENALGO_STRATEGY_EXCHANGE "
                f"(host calendar = {EXCHANGE})"
            )

    # ===========================================================================
    # WEBSOCKET HANDLER WITH IMMEDIATE EXIT
    # ===========================================================================

    def on_ltp_update(self, data):
        """Handle real-time LTP updates and place exit orders immediately"""
        if data.get("type") == "market_data" and data.get("symbol") == SYMBOL:
            self.ltp = float(data["data"]["ltp"])

            # Display current status
            current_time = datetime.now().strftime("%H:%M:%S")

            if self.position and not self.exit_in_progress:
                # Calculate real-time P&L
                if self.position == "BUY":
                    unrealized_pnl = (self.ltp - self.entry_price) * QUANTITY
                else:
                    unrealized_pnl = (self.entry_price - self.ltp) * QUANTITY

                pnl_sign = "+" if unrealized_pnl > 0 else "-"
                print(
                    f"\r[{current_time}] LTP: Rs.{self.ltp:.2f} | "
                    f"{self.position} @ Rs.{self.entry_price:.2f} | "
                    f"P&L: {pnl_sign}Rs.{abs(unrealized_pnl):.2f} | "
                    f"SL: {self.stoploss_price:.2f} | TG: {self.target_price:.2f}    ",
                    end="",
                )

                # Check and execute exit immediately
                exit_reason = None

                if self.position == "BUY":
                    if self.ltp <= self.stoploss_price:
                        exit_reason = "STOPLOSS HIT"
                        print(
                            f"\n[ALERT] STOPLOSS HIT! LTP Rs.{self.ltp:.2f} "
                            f"<= SL Rs.{self.stoploss_price:.2f}"
                        )
                    elif self.ltp >= self.target_price:
                        exit_reason = "TARGET HIT"
                        print(
                            f"\n[ALERT] TARGET HIT! LTP Rs.{self.ltp:.2f} "
                            f">= Target Rs.{self.target_price:.2f}"
                        )

                elif self.position == "SELL":
                    if self.ltp >= self.stoploss_price:
                        exit_reason = "STOPLOSS HIT"
                        print(
                            f"\n[ALERT] STOPLOSS HIT! LTP Rs.{self.ltp:.2f} "
                            f">= SL Rs.{self.stoploss_price:.2f}"
                        )
                    elif self.ltp <= self.target_price:
                        exit_reason = "TARGET HIT"
                        print(
                            f"\n[ALERT] TARGET HIT! LTP Rs.{self.ltp:.2f} "
                            f"<= Target Rs.{self.target_price:.2f}"
                        )

                # Place exit order immediately if SL/Target hit
                if exit_reason and not self.exit_in_progress:
                    self.exit_in_progress = True
                    print("[EXIT] Placing exit order immediately...")

                    # New thread for exit to avoid blocking WebSocket
                    exit_thread = threading.Thread(
                        target=self.place_exit_order,
                        args=(exit_reason,),
                    )
                    exit_thread.start()

            elif not self.position:
                print(
                    f"\r[{current_time}] LTP: Rs.{self.ltp:.2f} | No Position | "
                    f"Mode: {TRADE_DIRECTION} | Lookback: {self.lookback_days}d    ",
                    end="",
                )

    def websocket_thread(self):
        """WebSocket thread for real-time price updates"""
        try:
            print("[WEBSOCKET] Connecting...")
            self.client.connect()

            # Subscribe to LTP updates
            self.client.subscribe_ltp(self.instrument, on_data_received=self.on_ltp_update)
            print(f"[WEBSOCKET] Connected - Monitoring {SYMBOL} in real-time")

            # Keep thread alive
            while not self.stop_event.is_set():
                time.sleep(1)

        except Exception as e:
            print(f"\n[ERROR] WebSocket error: {e}")
        finally:
            print("\n[WEBSOCKET] Closing connection...")
            try:
                self.client.unsubscribe_ltp(self.instrument)
                self.client.disconnect()
            except Exception:
                pass
            print("[WEBSOCKET] Connection closed")

    # ===========================================================================
    # TRADING FUNCTIONS
    # ===========================================================================

    def get_historical_data(self):
        """Fetch historical candle data with configurable lookback"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)

            print(f"\n[DATA] Fetching {self.lookback_days} days of historical data...")
            print(
                f"[DATA] From: {start_date.strftime('%Y-%m-%d')} "
                f"To: {end_date.strftime('%Y-%m-%d')}"
            )

            data = self.client.history(
                symbol=SYMBOL,
                exchange=EXCHANGE,
                interval=CANDLE_TIMEFRAME,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )

            if data is not None and len(data) > 0:
                if "datetime" in data.columns:
                    first_time = str(data["datetime"].iloc[0])
                    last_time = str(data["datetime"].iloc[-1])
                    print(f"[DATA] Received {len(data)} candles from {first_time} to {last_time}")
                elif "date" in data.columns:
                    first_date = str(data["date"].iloc[0])
                    last_date = str(data["date"].iloc[-1])
                    print(f"[DATA] Received {len(data)} candles from {first_date} to {last_date}")
                else:
                    print(f"[DATA] Received {len(data)} candles")
            else:
                print("[WARNING] No data received from API")

            return data

        except Exception as e:
            print(f"\n[ERROR] Failed to fetch data: {str(e)}")
            print(f"[DEBUG] Error type: {type(e).__name__}")

            # Fallback attempt
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=self.lookback_days)

                data = self.client.history(
                    symbol=SYMBOL,
                    exchange=EXCHANGE,
                    interval=CANDLE_TIMEFRAME,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                )

                if data is not None and len(data) > 0:
                    print(f"[DATA] Successfully received {len(data)} candles (alternative method)")
                    return data

            except Exception as e2:
                print(f"[ERROR] Alternative fetch also failed: {str(e2)}")

            return None

    def check_for_signal(self, data):
        """Check for EMA crossover signals with direction filter"""
        if data is None:
            return None

        if len(data) < SLOW_EMA_PERIOD + 2:
            print(
                f"[INFO] Insufficient data. Need at least {SLOW_EMA_PERIOD + 2} candles, "
                f"have {len(data)}"
            )
            return None

        try:
            # Calculate EMAs
            data["fast_ema"] = data["close"].ewm(span=FAST_EMA_PERIOD, adjust=False).mean()
            data["slow_ema"] = data["close"].ewm(span=SLOW_EMA_PERIOD, adjust=False).mean()

            # Last three candles
            prev = data.iloc[-3]
            last = data.iloc[-2]
            current = data.iloc[-1]

            print(
                f"[DEBUG] Fast EMA: {last['fast_ema']:.2f}, "
                f"Slow EMA: {last['slow_ema']:.2f}, Close: {current['close']:.2f}"
            )

            # BUY signal
            if prev["fast_ema"] <= prev["slow_ema"] and last["fast_ema"] > last["slow_ema"]:
                if TRADE_DIRECTION in ["LONG", "BOTH"]:
                    print("[SIGNAL] BUY - Fast EMA crossed above Slow EMA")
                    return "BUY"
                print(f"[SIGNAL] BUY signal detected but ignored (Mode: {TRADE_DIRECTION})")
                return None

            # SELL signal
            if prev["fast_ema"] >= prev["slow_ema"] and last["fast_ema"] < last["slow_ema"]:
                if TRADE_DIRECTION in ["SHORT", "BOTH"]:
                    print("[SIGNAL] SELL - Fast EMA crossed below Slow EMA")
                    return "SELL"
                print(f"[SIGNAL] SELL signal detected but ignored (Mode: {TRADE_DIRECTION})")
                return None

        except Exception as e:
            print(f"[ERROR] Error checking signal: {str(e)}")

        return None

    def get_executed_price(self, order_id):
        """Get actual executed price from order status"""
        max_attempts = 5

        for _ in range(max_attempts):
            time.sleep(2)

            try:
                response = self.client.orderstatus(
                    order_id=order_id,
                    strategy=self.strategy_name,
                )

                if response.get("status") == "success":
                    order_data = response.get("data", {})

                    if order_data.get("order_status") == "complete":
                        executed_price = float(order_data.get("average_price", 0))
                        if executed_price > 0:
                            return executed_price

                    elif order_data.get("order_status") in ["rejected", "cancelled"]:
                        print(f"[ERROR] Order {order_data.get('order_status')}")
                        return None

                    else:
                        print(f"[WAITING] Order status: {order_data.get('order_status')}")

            except Exception as e:
                print(f"[ERROR] Failed to get order status: {e}")

        return None

    def place_entry_order(self, signal):
        """Place entry order based on direction filter"""
        if signal == "BUY" and TRADE_DIRECTION == "SHORT":
            print("[INFO] BUY signal ignored - SHORT only mode")
            return False

        if signal == "SELL" and TRADE_DIRECTION == "LONG":
            print("[INFO] SELL signal ignored - LONG only mode")
            return False

        print(f"\n[ORDER] Placing {signal} order for {QUANTITY} shares of {SYMBOL}")

        try:
            response = self.client.placeorder(
                strategy=self.strategy_name,
                symbol=SYMBOL,
                exchange=EXCHANGE,
                action=signal,
                quantity=QUANTITY,
                price_type="MARKET",
                product=PRODUCT,
            )

            if response.get("status") == "success":
                order_id = response.get("orderid")
                print(f"[ORDER] Order placed. ID: {order_id}")

                executed_price = self.get_executed_price(order_id)

                if executed_price:
                    self.position = signal
                    self.entry_price = executed_price

                    if signal == "BUY":
                        self.stoploss_price = round(self.entry_price - STOPLOSS, 2)
                        self.target_price = round(self.entry_price + TARGET, 2)
                    else:  # SELL
                        self.stoploss_price = round(self.entry_price + STOPLOSS, 2)
                        self.target_price = round(self.entry_price - TARGET, 2)

                    print("\n" + "=" * 60)
                    print(" TRADE EXECUTED")
                    print("=" * 60)
                    print(f" Direction Mode: {TRADE_DIRECTION}")
                    print(f" Position: {signal}")
                    print(f" Entry Price: Rs.{self.entry_price:.2f}")
                    print(f" Quantity: {QUANTITY}")
                    print(f" Stoploss: Rs.{self.stoploss_price:.2f}")
                    print(f" Target: Rs.{self.target_price:.2f}")
                    print("=" * 60)
                    print("\n[INFO] WebSocket monitoring SL/Target in real-time...")

                    self.exit_in_progress = False
                    return True

                print("[ERROR] Could not get executed price")
            else:
                print(f"[ERROR] Order failed: {response}")

        except Exception as e:
            print(f"[ERROR] Failed to place order: {e}")

        return False

    def place_exit_order(self, reason="Manual"):
        """Place exit order - called immediately from WebSocket handler"""
        if not self.position:
            self.exit_in_progress = False
            return

        exit_action = "SELL" if self.position == "BUY" else "BUY"
        print(f"\n[EXIT] Closing {self.position} position - {reason}")

        try:
            response = self.client.placeorder(
                strategy=self.strategy_name,
                symbol=SYMBOL,
                exchange=EXCHANGE,
                action=exit_action,
                quantity=QUANTITY,
                price_type="MARKET",
                product=PRODUCT,
            )

            if response.get("status") == "success":
                order_id = response.get("orderid")
                print(f"[EXIT] Exit order placed. ID: {order_id}")

                exit_price = self.get_executed_price(order_id)

                if exit_price:
                    if self.position == "BUY":
                        pnl = (exit_price - self.entry_price) * QUANTITY
                    else:
                        pnl = (self.entry_price - exit_price) * QUANTITY

                    print("\n" + "=" * 60)
                    print(" POSITION CLOSED")
                    print("=" * 60)
                    print(f" Reason: {reason}")
                    print(f" Exit Price: Rs.{exit_price:.2f}")
                    print(f" Entry Price: Rs.{self.entry_price:.2f}")
                    print(f" P&L: Rs.{pnl:.2f} [{'PROFIT' if pnl > 0 else 'LOSS'}]")
                    print("=" * 60)
                else:
                    print("[WARNING] Exit order placed but could not confirm price")

                # Reset position regardless
                self.position = None
                self.entry_price = 0
                self.stoploss_price = 0
                self.target_price = 0
                self.exit_in_progress = False

            else:
                print(f"[ERROR] Exit order failed: {response}")
                self.exit_in_progress = False  # Allow retry

        except Exception as e:
            print(f"[ERROR] Failed to exit: {e}")
            self.exit_in_progress = False  # Allow retry

    # ===========================================================================
    # STRATEGY THREAD
    # ===========================================================================

    def strategy_thread(self):
        """Strategy thread for signal generation only (exit handled by WebSocket)"""
        print("[STRATEGY] Strategy thread started")
        print(f"[STRATEGY] Direction: {TRADE_DIRECTION} trades only")
        print(f"[STRATEGY] Checking signals every {SIGNAL_CHECK_INTERVAL} seconds")
        print(f"[STRATEGY] Using {self.lookback_days} days of historical data")

        initial_data_fetched = False

        while not self.stop_event.is_set():
            try:
                if not self.position and not self.exit_in_progress:
                    data = self.get_historical_data()

                    if data is not None:
                        if not initial_data_fetched:
                            print(f"[STRATEGY] Initial data loaded: {len(data)} candles")
                            initial_data_fetched = True

                        signal = self.check_for_signal(data)
                        if signal:
                            self.place_entry_order(signal)
                    else:
                        if not initial_data_fetched:
                            print("[WARNING] Waiting for historical data...")

                time.sleep(SIGNAL_CHECK_INTERVAL)

            except Exception as e:
                print(f"\n[ERROR] Strategy error: {e}")
                time.sleep(10)

    # ===========================================================================
    # MAIN RUN METHOD
    # ===========================================================================

    def run(self):
        """Main method to run the bot"""
        print("=" * 60)
        print(" EMA CROSSOVER BOT")
        print("=" * 60)
        print(f" Symbol: {SYMBOL} | Exchange: {EXCHANGE}")
        print(f" Strategy: {FAST_EMA_PERIOD} EMA x {SLOW_EMA_PERIOD} EMA")
        print(f" Direction: {TRADE_DIRECTION} trades only")
        print(f" Risk: SL Rs.{STOPLOSS} | Target Rs.{TARGET}")
        print(f" Timeframe: {CANDLE_TIMEFRAME}")
        print(f" Lookback: {self.lookback_days} days")
        print(f" Signal Check: Every {SIGNAL_CHECK_INTERVAL} seconds")
        print("=" * 60)

        if TRADE_DIRECTION == "LONG":
            print(" [MODE] LONG ONLY - Will only take BUY trades")
        elif TRADE_DIRECTION == "SHORT":
            print(" [MODE] SHORT ONLY - Will only take SELL trades")
        else:
            print(" [MODE] BOTH - Will take both BUY and SELL trades")

        print("=" * 60)
        print("\nPress Ctrl+C to stop the bot\n")

        ws_thread = threading.Thread(target=self.websocket_thread, daemon=True)
        ws_thread.start()

        # Give WebSocket time to connect
        time.sleep(2)

        strat_thread = threading.Thread(target=self.strategy_thread, daemon=True)
        strat_thread.start()

        try:
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] Shutting down bot...")
            self.running = False
            self.stop_event.set()

            if self.position and not self.exit_in_progress:
                print("[INFO] Closing open position before shutdown...")
                self.place_exit_order("Bot Shutdown")

            ws_thread.join(timeout=5)
            strat_thread.join(timeout=5)

            print("[SUCCESS] Bot stopped successfully!")


# ===============================================================================
# START THE BOT
# ===============================================================================

if __name__ == "__main__":
    if not API_KEY or API_KEY == "openalgo-apikey":
        print(
            "[WARNING] OPENALGO_API_KEY is not set in environment. "
            "Set it before running in live mode."
        )

    print("\n" + "=" * 60)
    print(" OPENALGO EMA STRATEGY - READY TO RUN")
    print("=" * 60)
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Mode: {TRADE_DIRECTION}")
    print(f" Lookback: {LOOKBACK_DAYS} days")
    print("=" * 60 + "\n")

    bot = ConfigurableEMABot()
    bot.run()

```


---

# FILE: examples\python\expiry_dates.py

```py
"""
OpenAlgo Expiry Date Extraction Example
----------------------------------------
Demonstrates how to extract expiry dates using the OpenAlgo Python SDK.

Weekly: current_week, next_week, current_month, next_month
Monthly: current_month, next_month, far_month

Reference: AlgoMirror Strategy Executor implementation
"""

from datetime import datetime

from openalgo import api

# Initialize client with explicit parameters
client = api(
    api_key="7371cc58b9d30204e5fee1d143dc8cd926bcad90c24218201ad81735384d2752",  # Replace with your API key
    host="http://127.0.0.1:5000",  # Replace with your API host
)

# Expiry request parameters
symbol = "NIFTY"  # Index symbol (NIFTY, BANKNIFTY, SENSEX, etc.)
exchange = "NFO"  # Exchange (NFO for NIFTY/BANKNIFTY, BFO for SENSEX)
instrumenttype = "options"  # Instrument type ("options" or "futures")
expirytype = "weekly"  # Expiry type ("weekly" or "monthly")


def get_expiry_dates(symbol: str, exchange: str, instrumenttype: str, expirytype: str):
    """
    Fetch and categorize expiry dates from OpenAlgo API.

    Args:
        symbol: Index symbol (NIFTY, BANKNIFTY, SENSEX, etc.)
        exchange: Exchange (NFO for NIFTY/BANKNIFTY, BFO for SENSEX)
        instrumenttype: Instrument type ("options" or "futures")
        expirytype: Expiry type ("weekly" or "monthly")

    Returns:
        For weekly: dict with current_week, next_week, current_month, next_month
        For monthly: dict with current_month, next_month, far_month
    """
    # Fetch expiry dates from OpenAlgo
    response = client.expiry(symbol=symbol, exchange=exchange, instrumenttype=instrumenttype)

    if response.get("status") != "success":
        raise Exception(f"Failed to fetch expiries: {response.get('message')}")

    expiries = response.get("data", [])
    if not expiries:
        raise Exception(f"No expiries available for {symbol}")

    # Parse and sort expiries chronologically
    def parse_expiry(exp_str):
        """Parse expiry string to datetime"""
        formats = ["%d-%b-%y", "%d%b%y", "%d-%B-%y", "%d%B%y"]
        exp_upper = exp_str.upper().strip()
        for fmt in formats:
            try:
                return datetime.strptime(exp_upper, fmt)
            except ValueError:
                continue
        return datetime.max

    sorted_expiries = sorted(expiries, key=parse_expiry)

    # Extract expiry dates by category
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    next_month = (current_month % 12) + 1
    next_year = current_year + 1 if next_month == 1 else current_year
    far_month = (next_month % 12) + 1
    far_year = next_year + 1 if far_month == 1 else next_year

    if expirytype == "weekly":
        result = {
            "current_week": None,
            "next_week": None,
            "current_month": None,
            "next_month": None,
        }

        # Current week = nearest expiry (index 0)
        if sorted_expiries:
            result["current_week"] = sorted_expiries[0]

        # Next week = second expiry (index 1)
        if len(sorted_expiries) > 1:
            result["next_week"] = sorted_expiries[1]

        # Current month = last expiry of current calendar month
        for exp_str in sorted_expiries:
            exp_date = parse_expiry(exp_str)
            if exp_date.month == current_month and exp_date.year == current_year:
                result["current_month"] = exp_str  # Keep updating to get the last one

        # Next month = last expiry of next calendar month
        for exp_str in sorted_expiries:
            exp_date = parse_expiry(exp_str)
            if exp_date.month == next_month and exp_date.year == next_year:
                result["next_month"] = exp_str  # Keep updating to get the last one

    else:  # monthly
        result = {"current_month": None, "next_month": None, "far_month": None}

        # Current month = last expiry of current calendar month
        for exp_str in sorted_expiries:
            exp_date = parse_expiry(exp_str)
            if exp_date.month == current_month and exp_date.year == current_year:
                result["current_month"] = exp_str  # Keep updating to get the last one

        # Next month = last expiry of next calendar month
        for exp_str in sorted_expiries:
            exp_date = parse_expiry(exp_str)
            if exp_date.month == next_month and exp_date.year == next_year:
                result["next_month"] = exp_str  # Keep updating to get the last one

        # Far month = last expiry of far calendar month
        for exp_str in sorted_expiries:
            exp_date = parse_expiry(exp_str)
            if exp_date.month == far_month and exp_date.year == far_year:
                result["far_month"] = exp_str  # Keep updating to get the last one

    return result


# Example usage
if __name__ == "__main__":
    # Get expiries
    expiries = get_expiry_dates(
        symbol=symbol, exchange=exchange, instrumenttype=instrumenttype, expirytype=expirytype
    )

    print(f"{symbol} Expiry Dates ({expirytype}):")
    if expirytype == "weekly":
        print(f"  Current Week : {expiries['current_week']}")
        print(f"  Next Week    : {expiries['next_week']}")
        print(f"  Current Month: {expiries['current_month']}")
        print(f"  Next Month   : {expiries['next_month']}")
    else:  # monthly
        print(f"  Current Month: {expiries['current_month']}")
        print(f"  Next Month   : {expiries['next_month']}")
        print(f"  Far Month    : {expiries['far_month']}")

```


---

# FILE: examples\python\flask_optionchain.py

```py
from flask import Flask, jsonify, render_template_string, request
from openalgo import api

app = Flask(__name__)

# Initialize API client
client = api(
    api_key="83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0",
    host="http://127.0.0.1:5000",
)


# -----------------------------------------------------
# Color logic for CE/PE cells
# -----------------------------------------------------
def option_color(label):
    if not label:
        return "bg-base-200"

    lbl = label.upper()

    if lbl == "ATM":
        return "bg-yellow-400 text-black font-bold"

    if lbl.startswith("ITM"):
        return "bg-green-400/40 text-green-200"

    if lbl.startswith("OTM"):
        return "bg-red-400/40 text-red-200"

    return "bg-base-200"


# -----------------------------------------------------
# Option Chain UI — With Expiry + Strike Controls
# -----------------------------------------------------
@app.route("/")
def optionchain_ui():
    # Fetch expiry list
    expiry_data = client.expiry(symbol="NIFTY", exchange="NFO", instrumenttype="options")
    expiry_list = expiry_data.get("data", [])

    # Selected expiry (default = first)
    selected_expiry = request.args.get("expiry", expiry_list[0] if expiry_list else None)

    # Strike count selector (default = 10)
    strike_count = request.args.get("count", default=10, type=int)

    # Convert expiry "30-DEC-25" → "30DEC25" if needed
    api_expiry = selected_expiry.replace("-", "") if selected_expiry else None

    # Fetch option chain
    chain = client.optionchain(
        underlying="NIFTY", exchange="NSE_INDEX", expiry_date=api_expiry, strike_count=strike_count
    )

    # Template globals
    template_globals = {
        "option_color": option_color,
        "expiry_list": expiry_list,
        "selected_expiry": selected_expiry,
        "strike_count": strike_count,
    }

    # -----------------------------------------------------
    # HTML Template (Supabase Green Theme + DaisyUI)
    # -----------------------------------------------------
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>NIFTY Option Chain</title>

    <!-- DaisyUI + Tailwind CDN -->
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.css" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>

    <style>
        html, body { background: #0E0F19 !important; color: #E2E8F0; }
        .supabase-green { color: #3ECF8E !important; }
        .supabase-bg { background-color: #3ECF8E !important; }
        .supabase-border { border-color: #3ECF8E !important; }
        .hover-glow:hover { box-shadow: 0 0 12px #3ECF8E; }
    </style>
</head>

<body class="p-6">

<div class="max-w-7xl mx-auto">

    <h1 class="text-3xl font-bold text-center mb-4 supabase-green">
        NIFTY Option Chain (Supabase Theme)
    </h1>

    <!-- User Controls -->
    <form method="GET" class="flex flex-wrap items-center justify-center gap-4 mb-6">

        <!-- Expiry Selector -->
        <div>
            <label class="label">
                <span class="label-text supabase-green">Expiry Date</span>
            </label>
            <select name="expiry" class="select select-bordered w-48 supabase-border hover-glow bg-[#1A1B26]">
                {% for exp in expiry_list %}
                    <option value="{{ exp }}" {% if exp == selected_expiry %} selected {% endif %}>
                        {{ exp }}
                    </option>
                {% endfor %}
            </select>
        </div>

        <!-- Strike Count -->
        <div>
            <label class="label">
                <span class="label-text supabase-green"># of Strikes</span>
            </label>
            <input name="count"
                   type="number"
                   value="{{ strike_count }}"
                   min="1"
                   max="50"
                   class="input input-bordered w-32 supabase-border bg-[#1A1B26] hover-glow">
        </div>

        <!-- Submit -->
        <div class="mt-7">
            <button class="btn supabase-bg text-black hover-glow">Load</button>
        </div>
    </form>


    {% if chain["status"] != "success" %}
        <h2 class="text-red-400 text-center text-xl">Error: {{ chain.get("message") }}</h2>

    {% else %}

    <!-- Option Chain Table -->
    <div class="overflow-x-auto rounded-xl shadow-xl border supabase-border hover-glow">
    <table class="table w-full">
        <thead>
            <tr class="bg-[#2A2B37] text-center text-white">
                <th class="supabase-green">Strike</th>
                <th colspan="2" class="text-blue-300">CALLS (CE)</th>
                <th colspan="2" class="text-pink-300">PUTS (PE)</th>
            </tr>

            <tr class="bg-[#2A2B37] text-center">
                <th class="supabase-green">Strike</th>
                <th class="text-blue-300">LTP</th>
                <th class="text-blue-300">Label</th>
                <th class="text-pink-300">LTP</th>
                <th class="text-pink-300">Label</th>
            </tr>
        </thead>

        <tbody>
        {% for item in chain["chain"] %}
            {% set ce = item.ce %}
            {% set pe = item.pe %}
            {% set ce_class = option_color(ce.label if ce else '') %}
            {% set pe_class = option_color(pe.label if pe else '') %}

            <tr class="text-center hover:bg-[#2A2B37] transition">
                <!-- Strike column -->
                <td class="font-bold {% if item.strike == chain['atm_strike'] %} bg-yellow-500 text-black {% else %} supabase-green {% endif %}">
                    {{ item.strike }}
                </td>

                <!-- CE -->
                <td class="{{ ce_class }} font-semibold">{{ ce.ltp if ce else '-' }}</td>
                <td class="{{ ce_class }}">{{ ce.label if ce else '-' }}</td>

                <!-- PE -->
                <td class="{{ pe_class }} font-semibold">{{ pe.ltp if pe else '-' }}</td>
                <td class="{{ pe_class }}">{{ pe.label if pe else '-' }}</td>

            </tr>
        {% endfor %}
        </tbody>
    </table>
    </div>

    {% endif %}

</div>

</body>
</html>
"""

    # IMPORTANT — FIXED: pass template_globals ONLY ONCE
    return render_template_string(html, chain=chain, **template_globals)


# -----------------------------------------------------
# Run Flask
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)

```


---

# FILE: examples\python\heatmap.py

```py
import pandas as pd
import plotly.express as px
from openalgo import api

# ---------------------------------------------------
# OpenAlgo Client
# ---------------------------------------------------
client = api(
    api_key="7371cc58b9d30204e5fee1d143dc8cd926bcad90c24218201ad81735384d2752",
    host="http://127.0.0.1:5000",
)

print("🔁 OpenAlgo Python Bot is running.")

# ---------------------------------------------------
# NIFTY 50 SYMBOLS
# ---------------------------------------------------
symbols = [
    "INDIGO",
    "TRENT",
    "HINDUNILVR",
    "HCLTECH",
    "WIPRO",
    "INFY",
    "TATACONSUM",
    "TATASTEEL",
    "ITC",
    "ASIANPAINT",
    "SBILIFE",
    "LT",
    "SHRIRAMFIN",
    "BEL",
    "SBIN",
    "COALINDIA",
    "KOTAKBANK",
    "TCS",
    "SUNPHARMA",
    "MAXHEALTH",
    "NESTLEIND",
    "RELIANCE",
    "ETERNAL",
    "APOLLOHOSP",
    "ICICIBANK",
    "GRASIM",
    "ULTRACEMCO",
    "ADANIENT",
    "AXISBANK",
    "DRREDDY",
    "TECHM",
    "TMPV",
    "JIOFIN",
    "NTPC",
    "BAJFINANCE",
    "BHARTIARTL",
    "POWERGRID",
    "HINDALCO",
    "HDFCBANK",
    "TITAN",
    "HDFCLIFE",
    "MARUTI",
    "BAJAJFINSV",
    "ADANIPORTS",
    "CIPLA",
    "JSWSTEEL",
    "BAJAJ-AUTO",
    "ONGC",
    "EICHERMOT",
    "M&M",
]

# ---------------------------------------------------
# FETCH LIVE QUOTES
# ---------------------------------------------------
quote_symbols = [{"symbol": s, "exchange": "NSE"} for s in symbols]
response = client.multiquotes(symbols=quote_symbols)

rows = []

print("\n📊 Live Market Data:")
for item in response["results"]:
    symbol = item["symbol"]
    ltp = item["data"]["ltp"]
    prev_close = item["data"]["prev_close"]

    change_pct = round(((ltp - prev_close) / prev_close) * 100, 2)

    # Print immediately (rule)
    print(f"{symbol} | LTP: {ltp} | Change: {change_pct}%")

    rows.append([symbol, change_pct])

# ---------------------------------------------------
# PREPARE + SORT DATA
# ---------------------------------------------------
df = pd.DataFrame(rows, columns=["Symbol", "Change"])

# 🔥 SORT: TOP GAINERS → BOTTOM LOSERS
df = df.sort_values("Change", ascending=False).reset_index(drop=True)

# Grid: 10 columns x 5 rows
cols = 10
df["row"] = df.index // cols
df["col"] = df.index % cols

pivot_values = df.pivot(index="row", columns="col", values="Change")
pivot_labels = df.pivot(index="row", columns="col", values="Symbol")

# ---------------------------------------------------
# HEATMAP PLOT
# ---------------------------------------------------
fig = px.imshow(pivot_values, color_continuous_scale="RdYlGn", aspect="auto")

fig.update_traces(
    text=pivot_labels.values,
    texttemplate="%{text}<br>%{z:.2f}%",
    hovertemplate="Symbol: %{text}<br>Change: %{z:.2f}%",
)

fig.update_layout(
    title="🔥 NIFTY 50 Sorted Heatmap (%)",
    xaxis=dict(type="category", title=""),
    yaxis=dict(type="category", autorange="reversed", title=""),
    template="plotly_dark",
    height=600,
)

# ---------------------------------------------------
# SAVE IMAGE (NO HTML OUTPUT)
# ---------------------------------------------------
fig.write_image("nifty50_heatmap.png", width=1200, height=600, scale=2)

print("\n✅ Heatmap saved as nifty50_heatmap.png")

```


---

# FILE: examples\python\ltp_example.py

```py
"""
OpenAlgo WebSocket Feed Example
"""

import time

from openalgo import api

# Initialize feed client with explicit parameters
client = api(
    api_key="7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc",  # Replace with your API key
    host="http://127.0.0.1:5000",  # Replace with your API host
    ws_url="ws://127.0.0.1:8765",  # Explicit WebSocket URL (can be different from REST API host)
)

# MCX instruments for testing
instruments_list = [{"exchange": "NSE", "symbol": "TCS", "exchange": "NSE", "symbol": "INFY"}]


def on_data_received(data):
    print("LTP Update:")
    print(data)


# Connect and subscribe
client.connect()
client.subscribe_ltp(instruments_list, on_data_received=on_data_received)

# Poll LTP data a few times
for i in range(100):
    print(f"\nPoll {i + 1}:")
    print(client.get_ltp())
    time.sleep(0.5)

# Cleanup
client.unsubscribe_ltp(instruments_list)
client.disconnect()

```


---

# FILE: examples\python\margin_example.ipynb

[BINARY FILE]

Type: .ipynb

Size: 7930 bytes

Path: examples\python\margin_example.ipynb


---

# FILE: examples\python\multiquotes_example.py

```py
from openalgo import api

# Initialize client
client = api(
    api_key="c32eb9dee6673190bb9dfab5f18ef0a96b0d76ba484cd36bc5ca5f7ebc8745bf",
    host="http://127.0.0.1:5000",
)

# Fetch multiple quotes
response = client.multiquotes(
    symbols=[
        {"symbol": "RELIANCE", "exchange": "NSE"},
        {"symbol": "TCS", "exchange": "NSE"},
        {"symbol": "INFY", "exchange": "NSE"},
    ]
)

print(response)

```


---

# FILE: examples\python\Nifty OI Charts.py

```py
"""
NIFTY Option Chain - CE/PE Open Interest Histogram (Side by Side)
Author : OpenAlgo GPT
Description: Plots Option Chain OI histogram for NIFTY 27JAN26 expiry
             CE (green) and PE (red) bars SIDE BY SIDE
             Only 100-point strikes (no 50s)
             White background
"""

print("🔁 OpenAlgo Python Bot is running.")

from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from openalgo import api

# ───────────────────────── CONFIG ─────────────────────────
API_KEY = "3f75e26648a543a886c9b38332a6942e30e0710bbf0488cf432ef27745de8ae7"
API_HOST = "http://127.0.0.1:5000"

# Option Chain Parameters
UNDERLYING = "NIFTY"
EXCHANGE = "NSE_INDEX"
EXPIRY = "27JAN26"  # 27 January 2026 expiry
STRIKE_COUNT = 40  # Number of strikes around ATM
LOT_SIZE = 75  # NIFTY lot size
STRIKE_FILTER = 100  # Only show strikes divisible by 100

# ─────────────────────── INIT CLIENT ──────────────────────
client = api(api_key=API_KEY, host=API_HOST)


# ───────────────────── FETCH OPTION CHAIN ─────────────────────
def fetch_option_chain():
    """Fetch option chain data from OpenAlgo API"""

    print(f"\n📥 Fetching {UNDERLYING} Option Chain for {EXPIRY} expiry...")

    chain_data = client.optionchain(
        underlying=UNDERLYING, exchange=EXCHANGE, expiry_date=EXPIRY, strike_count=STRIKE_COUNT
    )

    print(f"Option Chain Response Status: {chain_data.get('status', 'N/A')}")

    if chain_data.get("status") != "success":
        raise ValueError(f"Failed to fetch option chain: {chain_data}")

    underlying_ltp = chain_data.get("underlying_ltp", 0)
    atm_strike = chain_data.get("atm_strike", 0)
    chain = chain_data.get("chain", [])

    print(f"✅ Underlying LTP: {underlying_ltp}")
    print(f"✅ ATM Strike: {atm_strike}")
    print(f"✅ Total Strikes (raw): {len(chain)}")

    return chain_data


# ───────────────────── PROCESS CHAIN DATA ─────────────────────
def process_chain_data(chain_data):
    """Process option chain into DataFrame for plotting"""

    chain = chain_data.get("chain", [])
    atm_strike = chain_data.get("atm_strike", 0)
    underlying_ltp = chain_data.get("underlying_ltp", 0)

    rows = []

    for item in chain:
        strike = item.get("strike", 0)

        # Filter: Only 100-point strikes (ignore 50s)
        if int(strike) % STRIKE_FILTER != 0:
            continue

        ce = item.get("ce", {})
        pe = item.get("pe", {})

        # Convert OI to lots
        ce_oi = ce.get("oi", 0)
        pe_oi = pe.get("oi", 0)
        ce_oi_lots = ce_oi // LOT_SIZE if ce_oi else 0
        pe_oi_lots = pe_oi // LOT_SIZE if pe_oi else 0

        rows.append(
            {
                "strike": int(strike),
                "ce_ltp": ce.get("ltp", 0),
                "pe_ltp": pe.get("ltp", 0),
                "ce_oi": ce_oi,
                "pe_oi": pe_oi,
                "ce_oi_lots": ce_oi_lots,
                "pe_oi_lots": pe_oi_lots,
                "ce_volume": ce.get("volume", 0),
                "pe_volume": pe.get("volume", 0),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values("strike").reset_index(drop=True)

    # Round ATM to nearest 100
    atm_strike_100 = int(round(atm_strike / 100) * 100)

    print(f"✅ Filtered Strikes (100s only): {len(df)}")
    print(f"📊 Strike Range: {df['strike'].min()} to {df['strike'].max()}")
    print(f"📊 Total CE OI (lots): {df['ce_oi_lots'].sum():,}")
    print(f"📊 Total PE OI (lots): {df['pe_oi_lots'].sum():,}")
    print(
        f"📊 PCR (OI): {df['pe_oi'].sum() / df['ce_oi'].sum():.2f}"
        if df["ce_oi"].sum() > 0
        else "   PCR: N/A"
    )

    return df, atm_strike_100, underlying_ltp


# ───────────────────── FORMAT NUMBER ─────────────────────
def format_num(x):
    """Format number as K for thousands"""
    if x >= 1000:
        return f"{x / 1000:.0f}K"
    return str(int(x))


# ───────────────────── PLOT OI HISTOGRAM SIDE BY SIDE ─────────────────────
def plot_oi_side_by_side(df, atm_strike, underlying_ltp, expiry):
    """Create OI histogram with CE and PE bars side by side"""

    fig = go.Figure()

    strikes = df["strike"].tolist()

    # CE OI - Green bars
    fig.add_trace(
        go.Bar(
            x=df["strike"].astype(str),
            y=df["ce_oi_lots"],
            name="Call OI",
            marker=dict(
                color="rgba(34, 197, 94, 0.9)",  # Green
                line=dict(color="rgba(22, 163, 74, 1)", width=1),
            ),
            text=[format_num(x) for x in df["ce_oi_lots"]],
            textposition="outside",
            textfont=dict(size=9, color="rgba(22, 163, 74, 1)"),
            customdata=np.column_stack(
                [
                    df["ce_oi_lots"],
                    df["pe_oi_lots"],
                    df["ce_ltp"],
                    df["pe_ltp"],
                ]
            ),
            hovertemplate=(
                "<b>Strike: %{x}</b><br>"
                "Call OI (lots): <b>%{customdata[0]:,.0f}</b><br>"
                "Put OI (lots): %{customdata[1]:,.0f}<br>"
                "Call Price: ₹%{customdata[2]:.2f}<br>"
                "Put Price: ₹%{customdata[3]:.2f}<br>"
                "<extra></extra>"
            ),
        )
    )

    # PE OI - Red bars
    fig.add_trace(
        go.Bar(
            x=df["strike"].astype(str),
            y=df["pe_oi_lots"],
            name="Put OI",
            marker=dict(
                color="rgba(239, 68, 68, 0.9)",  # Red
                line=dict(color="rgba(220, 38, 38, 1)", width=1),
            ),
            text=[format_num(x) for x in df["pe_oi_lots"]],
            textposition="outside",
            textfont=dict(size=9, color="rgba(220, 38, 38, 1)"),
            customdata=np.column_stack(
                [
                    df["ce_oi_lots"],
                    df["pe_oi_lots"],
                    df["ce_ltp"],
                    df["pe_ltp"],
                ]
            ),
            hovertemplate=(
                "<b>Strike: %{x}</b><br>"
                "Call OI (lots): %{customdata[0]:,.0f}<br>"
                "Put OI (lots): <b>%{customdata[1]:,.0f}</b><br>"
                "Call Price: ₹%{customdata[2]:.2f}<br>"
                "Put Price: ₹%{customdata[3]:.2f}<br>"
                "<extra></extra>"
            ),
        )
    )

    # Find ATM position for vertical line
    strike_list = df["strike"].astype(str).tolist()
    atm_str = str(atm_strike)

    if atm_str in strike_list:
        atm_idx = strike_list.index(atm_str)

        # Add ATM vertical line
        fig.add_shape(
            type="line",
            x0=atm_idx - 0.5,
            x1=atm_idx - 0.5,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(color="rgba(100, 100, 100, 0.7)", width=2, dash="dash"),
        )

        # ATM annotation
        fig.add_annotation(
            x=atm_idx,
            y=1.02,
            xref="x",
            yref="paper",
            text=f"ATM: {atm_strike}",
            showarrow=False,
            font=dict(size=11, color="black", family="Arial Black"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
            borderpad=3,
        )

    # PCR calculation
    total_ce = df["ce_oi"].sum()
    total_pe = df["pe_oi"].sum()
    pcr = total_pe / total_ce if total_ce > 0 else 0

    # Max OI strikes
    max_ce_strike = df.loc[df["ce_oi_lots"].idxmax(), "strike"]
    max_pe_strike = df.loc[df["pe_oi_lots"].idxmax(), "strike"]
    max_ce_oi = df["ce_oi_lots"].max()
    max_pe_oi = df["pe_oi_lots"].max()

    # Current time
    current_time = datetime.now().strftime("%d %b %Y %H:%M")

    # Layout - WHITE BACKGROUND
    fig.update_layout(
        title=dict(
            text=f"NIFTY {expiry} - current",
            x=0.5,
            font=dict(size=18, color="black", family="Arial"),
        ),
        xaxis=dict(
            title="Strike Price",
            type="category",
            tickangle=-45,
            tickfont=dict(size=9, color="black"),
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.5)",
            showline=True,
            linecolor="black",
            linewidth=1,
        ),
        yaxis=dict(
            title=dict(text="Open Interest (Lots)", font=dict(color="black")),
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.5)",
            tickformat=",d",
            tickfont=dict(color="black"),
            showline=True,
            linecolor="black",
            linewidth=1,
        ),
        # WHITE BACKGROUND
        template="plotly_white",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=600,
        width=1500,
        barmode="group",  # Side by side bars
        bargap=0.15,
        bargroupgap=0.05,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(color="black"),
        ),
        margin=dict(l=80, r=100, t=80, b=100),
        annotations=[
            # Timestamp
            dict(
                text=f"{current_time}",
                xref="paper",
                yref="paper",
                x=1,
                y=1.06,
                showarrow=False,
                font=dict(size=11, color="gray"),
                bgcolor="rgba(240,240,240,0.8)",
                borderpad=4,
            ),
            # PCR on right side
            dict(
                text=f"PCR: {pcr:.2f}",
                xref="paper",
                yref="paper",
                x=1.04,
                y=0.5,
                showarrow=False,
                font=dict(size=12, color="black", family="Arial Black"),
                textangle=-90,
            ),
            # Max OI info at bottom
            dict(
                text=f"Max CE OI: {max_ce_strike} ({format_num(max_ce_oi)}) | Max PE OI: {max_pe_strike} ({format_num(max_pe_oi)})",
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.18,
                showarrow=False,
                font=dict(size=10, color="gray"),
            ),
        ],
    )

    return fig


# ───────────────────── PRINT OI TABLE ─────────────────────
def print_oi_table(df, atm_strike):
    """Print top OI strikes"""

    print(f"\n{'=' * 70}")
    print("📊 TOP 10 STRIKES BY OI")
    print(f"{'=' * 70}")

    print("\n🟢 TOP 5 CALL OI (Resistance Levels):")
    top_ce = df.nlargest(5, "ce_oi_lots")[["strike", "ce_oi_lots", "ce_ltp"]]
    for _, row in top_ce.iterrows():
        marker = " ⬅️ ATM" if row["strike"] == atm_strike else ""
        print(
            f"   Strike {int(row['strike'])}: {int(row['ce_oi_lots']):>10,} lots | LTP: ₹{row['ce_ltp']:.2f}{marker}"
        )

    print("\n🔴 TOP 5 PUT OI (Support Levels):")
    top_pe = df.nlargest(5, "pe_oi_lots")[["strike", "pe_oi_lots", "pe_ltp"]]
    for _, row in top_pe.iterrows():
        marker = " ⬅️ ATM" if row["strike"] == atm_strike else ""
        print(
            f"   Strike {int(row['strike'])}: {int(row['pe_oi_lots']):>10,} lots | LTP: ₹{row['pe_ltp']:.2f}{marker}"
        )

    print(f"{'=' * 70}\n")


# ───────────────────── MAIN EXECUTION ─────────────────────
if __name__ == "__main__":
    try:
        # Fetch option chain
        chain_data = fetch_option_chain()

        # Process data (filter 100s only)
        df, atm_strike, underlying_ltp = process_chain_data(chain_data)

        # Print OI table
        print_oi_table(df, atm_strike)

        # Create side-by-side plot
        fig = plot_oi_side_by_side(df, atm_strike, underlying_ltp, EXPIRY)

        # Save and show
        output_file = f"nifty_oi_chain_{EXPIRY}.html"
        fig.write_html(output_file)
        print(f"📈 Chart saved to: {output_file}")

        fig.show()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

```


---

# FILE: examples\python\NiftyOI.ipynb

[BINARY FILE]

Type: .ipynb

Size: 48897 bytes

Path: examples\python\NiftyOI.ipynb


---

# FILE: examples\python\optionchain_example.py

```py
from openalgo import api

# Initialize client
client = api(
    api_key="83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0",
    host="http://127.0.0.1:5000",
)

# -------------------------------------------------------
# Get available expiry dates for NIFTY
# -------------------------------------------------------
expiry_result = client.expiry(
    symbol="NIFTY", exchange="NFO", instrumenttype="options", strike_count=10
)

if expiry_result["status"] == "success":
    print("Available NIFTY Expiries:")
    for exp in expiry_result["data"]:
        print(f"  {exp}")
else:
    print("Failed to fetch expiries :", expiry_result.get("message"))

# -------------------------------------------------------
# Get option chain (5 strikes around ATM)
# -------------------------------------------------------
chain = client.optionchain(
    underlying="NIFTY", exchange="NSE_INDEX", expiry_date="30DEC25", strike_count=5
)

print("\nNIFTY Option Chain (5 strikes around ATM):")
print("-" * 50)
print(chain)
print("-" * 50)
print("Strike  | CE LTP (Label) | PE LTP (Label)")

if chain["status"] == "success":
    print(f"\nUnderlying LTP: {chain['underlying_ltp']}")
    print(f"ATM Strike: {chain['atm_strike']}")

    print("\nStrike  | CE LTP (Label) | PE LTP (Label)")
    print("-" * 50)

    for item in chain["chain"]:
        ce = item.get("ce") or {}
        pe = item.get("pe") or {}

        print(
            f"{item['strike']:>7} | "
            f"{ce.get('ltp', '-'):>6} ({ce.get('label', '-'):>4}) | "
            f"{pe.get('ltp', '-'):>6} ({pe.get('label', '-'):>4})"
        )
else:
    print("Failed to fetch option chain :", chain.get("message"))

```


---

# FILE: examples\python\placing ATM order.py

```py
from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

# ------------------------------------------
# Initialize API client
# ------------------------------------------
client = api(
    api_key="83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0",
    host="http://127.0.0.1:5000",
)

# ------------------------------------------
# Fetch NIFTY Spot (must print immediately)
# ------------------------------------------
quote = client.quotes(symbol="NIFTY", exchange="NSE_INDEX")
print("NIFTY QUOTE:", quote)

# ------------------------------------------
# Place NIFTY ATM Option Order - 09DEC25
# ------------------------------------------
response = client.optionsorder(
    strategy="python",
    underlying="NIFTY",  # Underlying Index
    exchange="NSE_INDEX",  # Index exchange
    expiry_date="09DEC25",  # Correct expiry
    offset="OTM2",  # Auto-select ATM strike
    option_type="CE",  # CE or PE
    action="BUY",  # BUY or SELL
    quantity=75,  # 1 Lot = 75
    pricetype="MARKET",  # MARKET or LIMIT
    product="NRML",  # NRML or MIS
    splitsize=0,  # 0 = no split
)

print("ORDER RESPONSE:", response)

```


---

# FILE: examples\python\plotting candles.py

```py
"""
RELIANCE 5-Minute Candlestick Chart - Last 20 Days
With Bollinger Bands (Top) and RSI (Bottom)
Author : OpenAlgo GPT
Description: Plots RELIANCE 5m candlestick chart using Plotly with category x-axis
"""

print("🔁 OpenAlgo Python Bot is running.")

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from openalgo import api, ta
from plotly.subplots import make_subplots

# ───────────────────────── CONFIG ─────────────────────────
API_KEY = "3f75e26648a543a886c9b38332a6942e30e0710bbf0488cf432ef27745de8ae7"
API_HOST = "http://127.0.0.1:5000"

SYMBOL = "RELIANCE"
EXCHANGE = "NSE"
INTERVAL = "5m"

# Date range controls (last 20 days)
END_DATE = datetime.now().strftime("%Y-%m-%d")
START_DATE = (datetime.now() - pd.Timedelta(days=20)).strftime("%Y-%m-%d")

# ─────────────────────── INIT CLIENT ──────────────────────
client = api(api_key=API_KEY, host=API_HOST)


# ───────────────────── FETCH HISTORICAL DATA ─────────────────────
def fetch_historical_data():
    """Fetch 5m historical data for RELIANCE"""
    print(f"Fetching {SYMBOL} {INTERVAL} data from {START_DATE} to {END_DATE}...")

    response = client.history(
        symbol=SYMBOL,
        exchange=EXCHANGE,
        interval=INTERVAL,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    # Print the raw response
    print(f"History Response: {response}")

    # OpenAlgo history() returns DataFrame directly (not a dict)
    if isinstance(response, pd.DataFrame):
        df = response.copy()
    else:
        # Fallback if it returns dict
        df = pd.DataFrame(response.get("data", response))

    # Check if DataFrame is empty
    if df.empty:
        raise ValueError("No data received from API")

    # Handle index - if timestamp is already the index
    if df.index.name == "timestamp" or "timestamp" not in df.columns:
        df.index = pd.to_datetime(df.index)
    else:
        df["datetime"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("datetime")

    df = df.sort_index()

    # Standardize column names to lowercase
    df.columns = df.columns.str.lower()

    # Ensure we have OHLC columns
    required_cols = ["open", "high", "low", "close"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    print(f"Fetched {len(df)} candles")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    return df


# ───────────────────── INDICATOR SETTINGS ─────────────────────
RSI_PERIOD = 20
BB_PERIOD = 15
BB_STD_DEV = 2.0


# ───────────────────── CALCULATE INDICATORS ─────────────────────
def calculate_indicators(df: pd.DataFrame):
    """Calculate RSI and Bollinger Bands using OpenAlgo ta library"""

    # RSI (20)
    df["rsi"] = ta.rsi(df["close"], period=RSI_PERIOD)

    # Bollinger Bands (15, 2)
    bb_upper, bb_middle, bb_lower = ta.bbands(df["close"], period=BB_PERIOD, std_dev=BB_STD_DEV)
    df["bb_upper"] = bb_upper
    df["bb_middle"] = bb_middle
    df["bb_lower"] = bb_lower

    print(f"Calculated RSI({RSI_PERIOD}) and Bollinger Bands({BB_PERIOD}, {BB_STD_DEV})")

    return df


# ───────────────────── PLOT CANDLESTICK CHART ─────────────────────
def plot_candlestick(df: pd.DataFrame):
    """Create interactive candlestick chart with Bollinger Bands and RSI using Plotly"""

    # Create x-axis as category strings (Plotly requirement from docs)
    x_category = df.index.strftime("%d-%b<br>%H:%M").tolist()

    # Calculate tick positions (show ~15 labels for readability)
    total_candles = len(x_category)
    tick_step = max(1, total_candles // 15)
    tick_vals = [x_category[i] for i in range(0, total_candles, tick_step)]

    # Create subplots: Candlestick with BB (top 75%), RSI (bottom 25%)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
        subplot_titles=[
            f"{SYMBOL} ({EXCHANGE}) - {INTERVAL} with Bollinger Bands ({BB_PERIOD}, {BB_STD_DEV})",
            f"RSI ({RSI_PERIOD})",
        ],
    )

    # ───────── ROW 1: Candlestick + Bollinger Bands ─────────

    # Add candlestick trace
    fig.add_trace(
        go.Candlestick(
            x=x_category,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=SYMBOL,
            increasing_line_color="#26a69a",  # Green for bullish
            decreasing_line_color="#ef5350",  # Red for bearish
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # Bollinger Bands - Upper Band
    fig.add_trace(
        go.Scatter(
            x=x_category,
            y=df["bb_upper"],
            name="BB Upper",
            line=dict(color="rgba(173, 216, 230, 0.8)", width=1),
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # Bollinger Bands - Middle Band (SMA)
    fig.add_trace(
        go.Scatter(
            x=x_category,
            y=df["bb_middle"],
            name="BB Middle",
            line=dict(color="rgba(255, 165, 0, 0.8)", width=1, dash="dash"),
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # Bollinger Bands - Lower Band
    fig.add_trace(
        go.Scatter(
            x=x_category,
            y=df["bb_lower"],
            name="BB Lower",
            line=dict(color="rgba(173, 216, 230, 0.8)", width=1),
            fill="tonexty",  # Fill area between upper and lower bands
            fillcolor="rgba(173, 216, 230, 0.1)",
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # ───────── ROW 2: RSI ─────────

    # RSI Line
    fig.add_trace(
        go.Scatter(
            x=x_category,
            y=df["rsi"],
            name=f"RSI ({RSI_PERIOD})",
            line=dict(color="#ab47bc", width=1.5),
            showlegend=True,
        ),
        row=2,
        col=1,
    )

    # RSI Overbought Line (70)
    fig.add_hline(
        y=70,
        line_dash="dash",
        line_color="red",
        line_width=1,
        annotation_text="Overbought (70)",
        annotation_position="right",
        row=2,
        col=1,
    )

    # RSI Oversold Line (30)
    fig.add_hline(
        y=30,
        line_dash="dash",
        line_color="green",
        line_width=1,
        annotation_text="Oversold (30)",
        annotation_position="right",
        row=2,
        col=1,
    )

    # RSI Middle Line (50)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", line_width=1, row=2, col=1)

    # ───────── LAYOUT ─────────
    fig.update_layout(
        title=dict(
            text=f"{SYMBOL} Technical Analysis<br><sup>{START_DATE} to {END_DATE}</sup>",
            x=0.5,
            font=dict(size=18),
        ),
        template="plotly_dark",
        height=900,
        width=1400,
        hovermode="x unified",
        margin=dict(l=60, r=100, t=80, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis2=dict(rangeslider=dict(visible=False)),
    )

    # Update x-axes
    fig.update_xaxes(
        type="category",
        tickmode="array",
        tickvals=tick_vals,
        tickangle=-45,
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        rangeslider=dict(visible=False),
        row=1,
        col=1,
    )

    fig.update_xaxes(
        type="category",
        tickmode="array",
        tickvals=tick_vals,
        tickangle=-45,
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        title="Date / Time",
        row=2,
        col=1,
    )

    # Update y-axes
    fig.update_yaxes(
        title="Price (₹)",
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        tickformat=",.2f",
        row=1,
        col=1,
    )

    fig.update_yaxes(
        title="RSI",
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        range=[0, 100],  # RSI range is 0-100
        row=2,
        col=1,
    )

    return fig


# ───────────────────── MAIN EXECUTION ─────────────────────
if __name__ == "__main__":
    try:
        # Fetch data
        df = fetch_historical_data()

        # Calculate indicators (RSI and Bollinger Bands)
        df = calculate_indicators(df)

        # Create and display chart
        fig = plot_candlestick(df)

        # Save as HTML file
        output_file = "reliance_candlestick_chart.html"
        fig.write_html(output_file)
        print(f"\nChart saved to: {output_file}")

        # Show the chart (opens in browser)
        fig.show()

    except Exception as e:
        print(f"Error: {e}")
        raise

```


---

# FILE: examples\python\quote_example.py

```py
"""
OpenAlgo WebSocket Quote Feed Example
"""

import time

from openalgo import api

# Initialize feed client with explicit parameters
client = api(
    api_key="7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc",  # Replace with your API key
    host="http://127.0.0.1:5000",  # Replace with your API host
    ws_url="ws://127.0.0.1:8765",  # Explicit WebSocket URL (can be different from REST API host)
)

# MCX instruments for testing
instruments_list = [
    {"exchange": "NSE_INDEX", "symbol": "NIFTY"},
    {"exchange": "NSE", "symbol": "INFY"},
    {"exchange": "NSE", "symbol": "TCS"},
]


def on_data_received(data):
    print("Quote Update:")
    print(data)


# Connect and subscribe
client.connect()
client.subscribe_quote(instruments_list, on_data_received=on_data_received)

# Poll Quote data a few times
for i in range(100):
    print(f"\nPoll {i + 1}:")
    print(client.get_quotes())
    time.sleep(0.5)

# Cleanup
client.unsubscribe_quote(instruments_list)
client.disconnect()

```


---

# FILE: examples\python\seasonality.py

```py
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from openalgo import api

# ─── Configuration ───────────────────────────────────────────────
API_KEY = "9d5d445ffb2b55af20871a6142e2cedf8c1002e55fce8a93ebe7028b0a6b7cc4"
HOST = "http://127.0.0.1:5000"
SYMBOL = "ICICIBANK"
EXCHANGE = "NSE"
START_YEAR = 2015
COLOR_CUTOFF = 10  # max intensity cutoff (%)

# TradingView color theme
POS_COLOR = (8, 153, 129)    # #089981
NEG_COLOR = (242, 55, 69)    # #F23745
BG_COLOR = "#1e222d"
HEADER_BG = "rgba(128,128,128,0.2)"
TEXT_COLOR = "#d1d4dc"
LINE_COLOR = "rgba(128,128,128,0.3)"

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def calc_cell_color(value, cutoff=COLOR_CUTOFF):
    """Calculate cell background color matching TradingView's gradient logic."""
    if pd.isna(value):
        return "rgba(128,128,128,0.3)"

    base = POS_COLOR if value >= 0 else NEG_COLOR
    # Map absolute value to opacity range [0.10, 0.50] (light to heavy)
    intensity = min(abs(value) / cutoff, 1.0)
    opacity = 0.10 + intensity * 0.40
    return f"rgba({base[0]},{base[1]},{base[2]},{opacity})"


def calc_pos_pct_color(value, cutoff=50):
    """Color for Pos% row: treat (value - 50) as the signed value."""
    if pd.isna(value):
        return "rgba(128,128,128,0.3)"
    shifted = value - 50
    base = POS_COLOR if shifted >= 0 else NEG_COLOR
    intensity = min(abs(shifted) / cutoff, 1.0)
    opacity = 0.10 + intensity * 0.40
    return f"rgba({base[0]},{base[1]},{base[2]},{opacity})"


def fetch_monthly_data(client, symbol, exchange, start_year):
    """Fetch daily data and resample to monthly close prices."""
    start_date = f"{start_year - 1}-12-01"
    end_date = pd.Timestamp.now().strftime("%Y-%m-%d")

    df = client.history(
        symbol=symbol,
        exchange=exchange,
        interval="D",
        start_date=start_date,
        end_date=end_date
    )

    if df is None or df.empty:
        raise ValueError("No data returned from API. Check symbol/exchange/dates.")

    # Resample to monthly — use last close of each month
    monthly = df["close"].resample("ME").last()
    monthly = monthly.dropna()

    # Drop the current incomplete month — only keep fully completed months
    today = pd.Timestamp.now(tz=monthly.index.tz)
    last_complete_month_end = (today.replace(day=1) - pd.Timedelta(days=1)).normalize()
    monthly = monthly[monthly.index <= last_complete_month_end]

    return monthly


def build_seasonality_matrix(monthly_close, start_year):
    """Build year x month matrix of monthly % returns (prev month close to current month close)."""
    # Monthly return: (current_close - prev_close) / abs(prev_close) * 100
    returns = monthly_close.pct_change() * 100

    years = sorted(set(returns.index.year))
    years = [y for y in years if y >= start_year]

    matrix = pd.DataFrame(index=years, columns=range(1, 13), dtype=float)

    for dt, ret in returns.items():
        if dt.year >= start_year:
            matrix.loc[dt.year, dt.month] = ret

    return matrix


def build_heatmap_figure(matrix):
    """Build Plotly figure matching the TradingView seasonality heatmap."""
    years = list(matrix.index)
    n_years = len(years)

    # Calculate metrics
    avgs = [matrix[m].mean() for m in range(1, 13)]
    stdevs = [matrix[m].std(ddof=1) for m in range(1, 13)]
    pos_pcts = []
    for m in range(1, 13):
        col = matrix[m].dropna()
        pos_pcts.append((col >= 0).sum() / len(col) * 100 if len(col) > 0 else float("nan"))

    # Table columns: Year + 12 months
    header = ["Year"] + MONTH_NAMES

    # Total data rows: years + divider + avgs + stdev + pos%
    n_rows = n_years + 4

    # Build cell values and colors column by column (Plotly table format)
    cell_values = [[] for _ in range(13)]
    cell_colors = [[] for _ in range(13)]

    # Year rows
    for year in years:
        cell_values[0].append(str(year))
        cell_colors[0].append(HEADER_BG)
        for m in range(1, 13):
            val = matrix.loc[year, m]
            if pd.isna(val):
                cell_values[m].append("NaN%")
                cell_colors[m].append("rgba(128,128,128,0.3)")
            else:
                cell_values[m].append(f"{val:.2f}%")
                cell_colors[m].append(calc_cell_color(val))

    # Divider row
    for c in range(13):
        cell_values[c].append("")
        cell_colors[c].append(HEADER_BG)

    # Avgs row
    cell_values[0].append("Avgs:")
    cell_colors[0].append(HEADER_BG)
    for m in range(1, 13):
        val = avgs[m - 1]
        cell_values[m].append(f"{val:.2f}%")
        cell_colors[m].append(calc_cell_color(val))

    # StDev row
    cell_values[0].append("StDev:")
    cell_colors[0].append(HEADER_BG)
    for m in range(1, 13):
        val = stdevs[m - 1]
        cell_values[m].append(f"{val:.2f}")
        cell_colors[m].append("rgba(128,128,128,0.2)")

    # Pos% row
    cell_values[0].append("Pos%:")
    cell_colors[0].append(HEADER_BG)
    for m in range(1, 13):
        val = pos_pcts[m - 1]
        cell_values[m].append(f"{val:.0f}%")
        cell_colors[m].append(calc_pos_pct_color(val))

    fig = go.Figure(data=[go.Table(
        columnwidth=[80] + [100] * 12,
        header=dict(
            values=header,
            fill_color=HEADER_BG,
            font=dict(color=TEXT_COLOR, size=15, family="Trebuchet MS, sans-serif"),
            align="center",
            line=dict(color=LINE_COLOR, width=1),
            height=40,
        ),
        cells=dict(
            values=cell_values,
            fill_color=cell_colors,
            font=dict(color=TEXT_COLOR, size=14, family="Trebuchet MS, sans-serif"),
            align="center",
            line=dict(color=LINE_COLOR, width=1),
            height=36,
        ),
    )])

    fig.update_layout(
        title=dict(
            text=f"Seasonality — {SYMBOL} ({EXCHANGE}) Monthly Returns",
            font=dict(color=TEXT_COLOR, size=16, family="Trebuchet MS, sans-serif"),
            x=0.5,
        ),
        paper_bgcolor=BG_COLOR,
        margin=dict(l=10, r=10, t=50, b=10),
        height=max(400, 40 + n_rows * 36 + 60),
    )

    return fig


def main():
    client = api(api_key=API_KEY, host=HOST)

    print(f"Fetching daily data for {SYMBOL} on {EXCHANGE}...")
    monthly_close = fetch_monthly_data(client, SYMBOL, EXCHANGE, START_YEAR)
    print(f"Got {len(monthly_close)} monthly data points")

    matrix = build_seasonality_matrix(monthly_close, START_YEAR)
    print(f"Built seasonality matrix: {matrix.shape[0]} years x {matrix.shape[1]} months")
    print()

    # Print the matrix to console
    display_df = matrix.round(2).copy()
    display_df.columns = MONTH_NAMES
    print(display_df.to_string())
    print()

    # Build and show the Plotly heatmap
    fig = build_heatmap_figure(matrix)
    fig.show()
    print("Seasonality chart opened in browser.")


if __name__ == "__main__":
    main()

```


---

# FILE: examples\python\stoploss_example.py

```py
"""
🔁 OpenAlgo Python Bot is running.
"""

import time
from datetime import datetime

from openalgo import api

# Setup OpenAlgo client
client = api(
    api_key="your-openalgo-api-key",  # Replace with your API key
    host="http://127.0.0.1:5000",  # Replace with your API host
    ws_url="ws://127.0.0.1:8765",  # Explicit WebSocket URL (can be different from REST API host)
)

# Strategy details
STRATEGY_NAME = "LTP_Stoploss_Example"
SYMBOL = "GOLDPETAL30JUN25FUT"
EXCHANGE = "MCX"
QUANTITY = 1
PRODUCT = "MIS"
ACTION = "BUY"
PRICE_TYPE = "MARKET"
STOPLOSS_BUFFER = 5.0

order_id = None
entry_price = None
stoploss_price = None
ltp_hit = False


# Step 1: Place a buy order
def place_entry_order():
    global order_id
    print(f"Placing {ACTION} order for {SYMBOL}...")
    response = client.placeorder(
        strategy=STRATEGY_NAME,
        symbol=SYMBOL,
        exchange=EXCHANGE,
        action=ACTION,
        price_type=PRICE_TYPE,
        product=PRODUCT,
        quantity=QUANTITY,
    )
    print("Place Order Response:", response)
    if response.get("status") == "success":
        order_id = response.get("orderid")
        return True
    return False


# Step 2: Get order status and price
def wait_for_execution():
    global entry_price, stoploss_price
    print(f"Waiting for order execution: {order_id}")
    for _ in range(20):
        status_resp = client.orderstatus(order_id=order_id, strategy=STRATEGY_NAME)
        data = status_resp.get("data", {})
        order_status = data.get("order_status", "").lower()

        if order_status == "complete":
            entry_price = float(data["price"])
            stoploss_price = round(entry_price - STOPLOSS_BUFFER, 1)
            print("✅ Order completed!")
            print(f"🔹 Entry Price : {entry_price}")
            print(f"🔸 Stoploss    : {stoploss_price}")
            return True
        elif order_status == "rejected":
            print("❌ Order was rejected. Exiting.")
            exit(1)
        time.sleep(1)

    print("❌ Order not completed in time. Exiting.")
    exit(1)


# Step 3: LTP Callback
def on_data_received(data):
    global ltp_hit
    if data.get("type") == "market_data" and data.get("symbol") == SYMBOL:
        ltp = float(data["data"]["ltp"])
        timestamp = data["data"]["timestamp"]
        print(f"LTP {EXCHANGE}:{SYMBOL}: {ltp} | Time: {timestamp}")
        if not ltp_hit and ltp <= stoploss_price:
            ltp_hit = True
            print(f"🛑 Stoploss hit at LTP {ltp}. Sending exit order...")
            send_exit_order()


# Step 4: Exit order logic
def send_exit_order():
    response = client.placeorder(
        strategy=STRATEGY_NAME,
        symbol=SYMBOL,
        exchange=EXCHANGE,
        action="SELL",
        price_type="MARKET",
        product=PRODUCT,
        quantity=QUANTITY,
    )
    print("Exit Order Response:", response)


# === Main Execution ===
if __name__ == "__main__":
    print("🔁 OpenAlgo Python Bot is running.")

    if place_entry_order() and wait_for_execution():
        try:
            client.connect()
            client.subscribe_ltp([{"exchange": EXCHANGE, "symbol": SYMBOL}], on_data_received)

            print("📡 Monitoring LTP for stoploss...")
            while not ltp_hit:
                time.sleep(1)

        except KeyboardInterrupt:
            print("🛑 CTRL+C received. Shutting down gracefully...")

        finally:
            client.unsubscribe_ltp([{"exchange": EXCHANGE, "symbol": SYMBOL}])
            client.disconnect()
            print("🔌 Disconnected from WebSocket.")

```


---

# FILE: examples\python\stoploss_target_example.py

```py
"""
CRUDEOIL Buy Order with Websocket-Based SL/Target Monitoring
Stop Loss: 10 points | Target: 10 points
"""

import time

from openalgo import api

# Configuration
API_KEY = "your-api-key-here"
HOST = "http://127.0.0.1:5000"
WS_URL = "ws://127.0.0.1:8765"

SYMBOL = "CRUDEOIL16JAN26FUT"
EXCHANGE = "MCX"
QUANTITY = 100
PRODUCT = "NRML"
STRATEGY = "SL_Target_Bot"

STOP_LOSS_POINTS = 3
TARGET_POINTS = 3

# Global variables
entry_price = 0
stop_loss = 0
target = 0
position_active = False
client = None


def place_entry_order():
    """Place market buy order"""
    response = client.placeorder(
        strategy=STRATEGY,
        symbol=SYMBOL,
        action="BUY",
        exchange=EXCHANGE,
        price_type="MARKET",
        product=PRODUCT,
        quantity=QUANTITY,
    )
    print(f"Entry Order Response: {response}")
    return response


def get_fill_price(order_id):
    """Get average fill price from order status"""
    # Wait a moment for order to fill
    time.sleep(1)

    response = client.orderstatus(order_id=order_id, strategy=STRATEGY)
    print(f"Order Status: {response}")

    # average_price is nested inside 'data'
    data = response.get("data", {})
    avg_price = float(data.get("average_price", 0))
    return avg_price


def exit_position(reason):
    """Exit the position"""
    global position_active
    print(f"\n>>> EXIT TRIGGERED: {reason}")
    response = client.placeorder(
        strategy=STRATEGY,
        symbol=SYMBOL,
        action="SELL",
        exchange=EXCHANGE,
        price_type="MARKET",
        product=PRODUCT,
        quantity=QUANTITY,
    )
    print(f"Exit Order Response: {response}")
    position_active = False
    return response


def on_ltp_update(data):
    """Callback for LTP updates - check SL/Target"""
    global position_active, stop_loss, target, entry_price

    if not position_active:
        return

    try:
        ltp = float(data["data"]["ltp"])

        print(
            f"LTP: {ltp:.2f} | Entry: {entry_price:.2f} | SL: {stop_loss:.2f} | Target: {target:.2f}",
            end="\r",
        )

        # Check stop loss
        if ltp <= stop_loss:
            exit_position(f"STOP LOSS HIT at {ltp:.2f}")

        # Check target
        elif ltp >= target:
            exit_position(f"TARGET HIT at {ltp:.2f}")

    except Exception as e:
        print(f"Error processing update: {e}")


def main():
    global client, entry_price, stop_loss, target, position_active

    # Initialize client with WebSocket
    client = api(api_key=API_KEY, host=HOST, ws_url=WS_URL, verbose=True)

    print("=" * 50)
    print("CRUDEOIL BUY - SL/Target Monitor")
    print(f"Stop Loss: {STOP_LOSS_POINTS} pts | Target: {TARGET_POINTS} pts")
    print("=" * 50)

    # Step 1: Place entry order
    print("\nPlacing BUY order...")
    entry_response = place_entry_order()

    if entry_response.get("status") != "success":
        print(f"Order failed: {entry_response}")
        return

    order_id = entry_response.get("orderid")
    print(f"Order ID: {order_id}")

    # Step 2: Get fill price from order status
    print("\nFetching fill price from order status...")
    entry_price = get_fill_price(order_id)

    if entry_price <= 0:
        print("Failed to get fill price. Exiting.")
        return

    # Calculate SL and Target
    stop_loss = entry_price - STOP_LOSS_POINTS
    target = entry_price + TARGET_POINTS

    print(f"\nEntry Price: {entry_price:.2f}")
    print(f"Stop Loss: {stop_loss:.2f}")
    print(f"Target: {target:.2f}")

    position_active = True

    # Step 3: Connect to WebSocket for monitoring
    print("\nConnecting to WebSocket...")
    client.connect()

    instruments = [{"exchange": EXCHANGE, "symbol": SYMBOL}]
    client.subscribe_ltp(instruments, on_data_received=on_ltp_update)

    print("Monitoring for SL/Target... Press Ctrl+C to exit\n")

    # Keep running until position exits
    try:
        while position_active:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nManual exit requested...")

    # Cleanup
    print("Cleaning up...")
    client.unsubscribe_ltp(instruments)
    client.disconnect()
    print("Done.")


if __name__ == "__main__":
    main()

```


---

# FILE: examples\python\straddle_scheduler.py

```py
import time

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

# ===============================
# OpenAlgo Client
# ===============================
client = api(
    api_key="83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0",
    host="http://127.0.0.1:5000",
)

NIFTY_LOT = 75  # NSE Index lot size
LOTS = 1  # Number of lots


# ===============================
# Function to Place Straddle
# ===============================
def place_nifty_straddle_0920():
    try:
        # Fetch NIFTY INDEX Quote (must print immediately)
        quote = client.quotes(symbol="NIFTY", exchange="NSE_INDEX")
        print("NIFTY QUOTE:", quote)

        qty = LOTS * NIFTY_LOT

        # Place optionsmultiorder short straddle
        response = client.optionsmultiorder(
            strategy="NIFTY_09DEC25_STRADDLE_0920",
            underlying="NIFTY",
            exchange="NSE_INDEX",
            expiry_date="09DEC25",  # FIXED EXPIRY
            legs=[
                {
                    "offset": "ATM",
                    "option_type": "CE",
                    "action": "SELL",
                    "quantity": qty,
                    "product": "NRML",
                },
                {
                    "offset": "ATM",
                    "option_type": "PE",
                    "action": "SELL",
                    "quantity": qty,
                    "product": "NRML",
                },
            ],
        )

        print("ORDER RESPONSE:", response)

    except Exception as e:
        print("Error:", e)


# ===============================
# Schedule the Job at 09:20 IST
# ===============================
def schedule_straddle():
    ist = pytz.timezone("Asia/Kolkata")

    scheduler = BackgroundScheduler(timezone=ist)

    scheduler.add_job(
        place_nifty_straddle_0920,
        trigger="cron",
        day_of_week="mon-sun",
        hour=9,
        minute=20,
        id="nifty_0920_straddle",
    )

    scheduler.start()
    print("✅ Scheduled NIFTY 09DEC25 ATM Straddle for 09:20 IST (Mon–Sun).")

    return scheduler


if __name__ == "__main__":
    scheduler = schedule_straddle()

    # Keep script alive
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

```


---

# FILE: examples\python\straddle_with_stops.py

```py
import time

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

# =====================================
# OpenAlgo Client
# =====================================
client = api(
    api_key="83ad96143dd5081d033abcfd20e9108daee5708fbea404121a762bed1e498dd0",
    host="http://127.0.0.1:5000",
)

NIFTY_LOT = 75
LOTS = 1


# =====================================
# STOPLOSS USING placeorder
# =====================================
def place_stoploss_order(symbol, sl_trigger, quantity):
    sl_price = round(sl_trigger + 2, 2)  # Trigger + 2 buffer for SL-LIMIT

    print(f"🔻 Sending SL Order → {symbol}")
    print(f"Trigger: {sl_trigger} | Price: {sl_price}")

    response = client.placeorder(
        strategy="NIFTY_09DEC25_STOPLOSS",
        symbol=symbol,
        action="BUY",  # BUY to exit short position
        exchange="NFO",
        price_type="SL",  # STOPLOSS-LIMIT order
        product="NRML",
        quantity=str(quantity),
        price=str(sl_price),
        trigger_price=str(sl_trigger),
        disclosed_quantity="0",
    )

    print("SL ORDER RESPONSE:", response)
    return response


# =====================================
# MAIN STRATEGY: ENTRY + STOPLOSS
# =====================================
def place_nifty_straddle_with_sl():
    print("\n🔥 Scheduled Trigger — Placing NIFTY Straddle...")

    # STEP 1 — Fetch NIFTY quote
    quote = client.quotes(symbol="NIFTY", exchange="NSE_INDEX")
    print("NIFTY QUOTE:", quote)

    qty = LOTS * NIFTY_LOT

    # STEP 2 — ENTRY using optionsmultiorder
    entry = client.optionsmultiorder(
        strategy="NIFTY_09DEC25_STRADDLE",
        underlying="NIFTY",
        exchange="NSE_INDEX",
        legs=[
            {
                "offset": "ATM",
                "option_type": "CE",
                "action": "SELL",
                "quantity": qty,
                "expiry_date": "09DEC25",
                "product": "NRML",
                "pricetype": "MARKET",
                "splitsize": 0,
            },
            {
                "offset": "ATM",
                "option_type": "PE",
                "action": "SELL",
                "quantity": qty,
                "expiry_date": "09DEC25",
                "product": "NRML",
                "pricetype": "MARKET",
                "splitsize": 0,
            },
        ],
    )

    print("ENTRY ORDER RESPONSE:", entry)

    ce_leg = entry["results"][0]
    pe_leg = entry["results"][1]

    ce_orderid = ce_leg["orderid"]
    pe_orderid = pe_leg["orderid"]

    ce_symbol = ce_leg["symbol"]
    pe_symbol = pe_leg["symbol"]

    # STEP 3 — Wait for execution
    time.sleep(5)

    # STEP 4 — Fetch average filled prices
    ce_status = client.orderstatus(order_id=ce_orderid, strategy="NIFTY_09DEC25_STRADDLE")
    pe_status = client.orderstatus(order_id=pe_orderid, strategy="NIFTY_09DEC25_STRADDLE")

    print("CE ORDERSTATUS:", ce_status)
    print("PE ORDERSTATUS:", pe_status)

    ce_entry = float(ce_status["data"]["average_price"])
    pe_entry = float(pe_status["data"]["average_price"])

    # STEP 5 — Calculate 30% Stoploss
    ce_sl_trigger = round(ce_entry * 1.30, 2)
    pe_sl_trigger = round(pe_entry * 1.30, 2)

    print(f"CE SL Trigger = {ce_sl_trigger}")
    print(f"PE SL Trigger = {pe_sl_trigger}")

    # STEP 6 — Place SL Orders using only placeorder
    place_stoploss_order(symbol=ce_symbol, sl_trigger=ce_sl_trigger, quantity=qty)

    place_stoploss_order(symbol=pe_symbol, sl_trigger=pe_sl_trigger, quantity=qty)

    print("\n🎯 All Stoploss Orders Placed Successfully.")


# =====================================
# SCHEDULER — 09:20 AM IST
# =====================================
def schedule_straddle():
    ist = pytz.timezone("Asia/Kolkata")
    scheduler = BackgroundScheduler(timezone=ist)

    scheduler.add_job(
        place_nifty_straddle_with_sl,
        trigger="cron",
        day_of_week="mon-sun",
        hour=20,
        minute=49,
        id="nifty_straddle_0920",
    )

    scheduler.start()
    print("✅ Scheduled NIFTY 09DEC25 Straddle + SL at 20:49 AM IST (Mon–Sun)")
    return scheduler


if __name__ == "__main__":
    scheduler = schedule_straddle()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

```


---

# FILE: examples\python\supertrend.py

```py
import threading
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from openalgo import api

# Get API key from openalgo portal
api_key = "your-openalgo-api-key"

# Set the strategy details and trading parameters
strategy = "Supertrend Python"
symbol = "RELIANCE"  # OpenAlgo Symbol
exchange = "NSE"
product = "MIS"
quantity = 1

# Supertrend indicator inputs
atr_period = 5
atr_multiplier = 1.0

# Set the API Key
client = api(api_key=api_key, host="http://127.0.0.1:5000")


def Supertrend(df, atr_period, multiplier):
    """
    Calculate the Supertrend indicator.
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    # Calculate ATR using ewm like original code
    price_diffs = [high - low, high - close.shift(), close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    atr = true_range.ewm(alpha=1 / atr_period, min_periods=atr_period).mean()

    hl2 = (high + low) / 2
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)

    # Initialize supertrend array with boolean values like original code
    supertrend = [True] * len(df)

    for i in range(1, len(df.index)):
        curr, prev = i, i - 1

        if close.iloc[curr] > final_upperband.iloc[prev]:
            supertrend[curr] = True
        elif close.iloc[curr] < final_lowerband.iloc[prev]:
            supertrend[curr] = False
        else:
            supertrend[curr] = supertrend[prev]

            if supertrend[curr] == True and final_lowerband.iloc[curr] < final_lowerband.iloc[prev]:
                final_lowerband.iat[curr] = final_lowerband.iat[prev]
            if (
                supertrend[curr] == False
                and final_upperband.iloc[curr] > final_upperband.iloc[prev]
            ):
                final_upperband.iat[curr] = final_upperband.iat[prev]

        if supertrend[curr] == True:
            final_upperband.iat[curr] = np.nan
        else:
            final_lowerband.iat[curr] = np.nan

    return pd.DataFrame(
        {
            "Supertrend": supertrend,
            "Final_Lowerband": final_lowerband,
            "Final_Upperband": final_upperband,
        },
        index=df.index,
    )


def supertrend_strategy():
    """
    The Supertrend trading strategy.
    """
    position = 0

    while True:
        try:
            # Dynamic date range: 7 days back to today
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            # Fetch 1-minute historical data using OpenAlgo
            df = client.history(
                symbol=symbol,
                exchange=exchange,
                interval="1m",
                start_date=start_date,
                end_date=end_date,
            )

            # Check for valid data
            if df.empty:
                print("DataFrame is empty. Retrying...")
                time.sleep(15)
                continue

            # Verify required columns
            expected_columns = {"close", "high", "low", "open"}
            missing_columns = expected_columns - set(df.columns)
            if missing_columns:
                raise KeyError(f"Missing columns in DataFrame: {missing_columns}")

            # Round the close column
            df["close"] = df["close"].round(2)

            # Calculate Supertrend
            supertrend = Supertrend(df, atr_period, atr_multiplier)

            # Generate signals using original logic
            is_uptrend = supertrend["Supertrend"]
            longentry = is_uptrend.iloc[-2] and not is_uptrend.iloc[-3]
            shortentry = is_uptrend.iloc[-3] and not is_uptrend.iloc[-2]

            # Execute Buy Order
            if longentry and position <= 0:
                position = quantity
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="BUY",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity,
                    position_size=position,
                )
                print("Buy Order Response:", response)

            # Execute Sell Order
            elif shortentry and position >= 0:
                position = quantity * -1
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="SELL",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity,
                    position_size=position,
                )
                print("Sell Order Response:", response)

            # Log strategy information
            print("\nStrategy Status:")
            print("-" * 50)
            print(f"Position: {position}")
            print(f"LTP: {df['close'].iloc[-1]}")
            print(f"Supertrend: {supertrend['Supertrend'].iloc[-2]}")
            print(f"LowerBand: {supertrend['Final_Lowerband'].iloc[-2]:.2f}")
            print(f"UpperBand: {supertrend['Final_Upperband'].iloc[-2]:.2f}")
            print(f"Buy Signal: {longentry}")
            print(f"Sell Signal: {shortentry}")
            print("-" * 50)

        except Exception as e:
            print(f"Error in strategy: {str(e)}")
            time.sleep(15)
            continue

        # Wait before the next cycle
        time.sleep(15)


if __name__ == "__main__":
    print("Starting Supertrend Strategy...")
    supertrend_strategy()

```


---

# FILE: examples\python\test_2340_symbols.py

```py
"""
Test 2340 symbols subscription on single pooled connection
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
from datetime import datetime

from openalgo import api

# Initialize client
client = api(
    api_key="7653f710c940cdf1d757b5a7d808a60f43bc7e9c0239065435861da2869ec0fc",
    host="http://127.0.0.1:5000",
    ws_url="ws://127.0.0.1:8765",
)

# Stats tracking
stats = {"updates": 0, "symbols_with_data": set(), "lock": threading.Lock()}


def on_data(data):
    with stats["lock"]:
        stats["updates"] += 1
        if "symbol" in data:
            stats["symbols_with_data"].add(data["symbol"])


def load_symbols(csv_path, limit=2340):
    """Load symbols from CSV"""
    symbols = []
    paths = [
        csv_path,
        "NSE_SYMBOLS.csv",
        os.path.join(os.path.dirname(__file__), "NSE_SYMBOLS.csv"),
        os.path.join(os.path.dirname(__file__), "../../../NSE_SYMBOLS.csv"),
        "D:/Marketcalls/Openalgo_order_mode/NSE_SYMBOLS.csv",
    ]

    for path in paths:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    symbol = line.strip()
                    if symbol and not symbol.startswith("#"):
                        symbols.append({"exchange": "NSE", "symbol": symbol})
            print(f"Loaded {len(symbols)} symbols from {path}")
            return symbols

    print("CSV not found, using generated symbols")
    return [{"exchange": "NSE", "symbol": f"SYM{i}"} for i in range(limit)]


def main():
    print("=" * 60)
    print("2340 SYMBOLS SUBSCRIPTION TEST")
    print("=" * 60)

    # Load symbols
    symbols = load_symbols("NSE_SYMBOLS.csv", 2340)
    print(f"Total symbols to subscribe: {len(symbols)}")

    # Connect
    print("\nConnecting...")
    client.connect()
    ws_id = id(client.ws) if hasattr(client, "ws") and client.ws else None
    print(f"Connected! WebSocket ID: {ws_id}")

    # Subscribe in batches
    batch_size = 100
    print(f"\nSubscribing in batches of {batch_size}...")

    start_time = time.time()
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        client.subscribe_ltp(batch, on_data_received=on_data)

        # Check connection is still the same
        current_ws_id = id(client.ws) if hasattr(client, "ws") and client.ws else None
        batch_num = i // batch_size + 1
        total_batches = (len(symbols) + batch_size - 1) // batch_size

        if batch_num % 5 == 0 or batch_num == total_batches:
            print(
                f"  Batch {batch_num}/{total_batches} - WS ID: {current_ws_id} - Same: {current_ws_id == ws_id}"
            )

        time.sleep(0.3)

    subscribe_time = time.time() - start_time
    print(f"\nSubscription complete in {subscribe_time:.2f}s")

    # Monitor for 30 seconds
    print("\nMonitoring for 30 seconds...")
    monitor_start = time.time()

    while time.time() - monitor_start < 30:
        time.sleep(5)
        with stats["lock"]:
            print(
                f"  Updates: {stats['updates']:,} | Active symbols: {len(stats['symbols_with_data'])}"
            )

    # Final stats
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Subscribed symbols: {len(symbols)}")
    print(f"Symbols receiving data: {len(stats['symbols_with_data'])}")
    print(f"Total updates: {stats['updates']:,}")
    print(f"Connection reused: {id(client.ws) == ws_id}")
    print(f"WebSocket ID (final): {id(client.ws) if hasattr(client, 'ws') and client.ws else None}")
    print("=" * 60)

    # Cleanup
    print("\nDisconnecting...")
    client.disconnect()
    print("Done!")


if __name__ == "__main__":
    main()

```


---

# FILE: examples\python\webhook.ipynb

[BINARY FILE]

Type: .ipynb

Size: 2622 bytes

Path: examples\python\webhook.ipynb


---

# FILE: examples\python\whatsapp_quote_alert.ipynb

[BINARY FILE]

Type: .ipynb

Size: 5894 bytes

Path: examples\python\whatsapp_quote_alert.ipynb


---

# FILE: examples\python\william vix fix.py

```py
"""
RELIANCE 5-Minute Chart with Williams Vix Fix (CM_Williams_Vix_Fix)
Author : OpenAlgo GPT
Description: Plots RELIANCE candlestick with Williams Vix Fix indicator
             Converted from Pine Script v3 to Python using OpenAlgo ta library
"""

print("🔁 OpenAlgo Python Bot is running.")

from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from openalgo import api, ta
from plotly.subplots import make_subplots

# ───────────────────────── CONFIG ─────────────────────────
API_KEY = "3f75e26648a543a886c9b38332a6942e30e0710bbf0488cf432ef27745de8ae7"
API_HOST = "http://127.0.0.1:5000"

SYMBOL = "NIFTY"
EXCHANGE = "NSE_INDEX"
INTERVAL = "D"

# Date range controls (last 20 days)
END_DATE = datetime.now().strftime("%Y-%m-%d")
START_DATE = (datetime.now() - pd.Timedelta(days=200)).strftime("%Y-%m-%d")

# ───────────────────────── WILLIAMS VIX FIX PARAMETERS ─────────────────────────
# Pine Script original parameters
WVF_LOOKBACK = 22  # pd = LookBack Period Standard Deviation High
BB_LENGTH = 20  # bbl = Bollinger Band Length
BB_MULT = 2.0  # mult = Bollinger Band Standard Deviation Up
PERCENTILE_LOOKBACK = 50  # lb = Look Back Period Percentile High
PERCENTILE_HIGH = 0.85  # ph = Highest Percentile (0.85 = 85%)
PERCENTILE_LOW = 1.01  # pl = Lowest Percentile

# Display options
SHOW_HIGH_RANGE = True  # hp = Show High Range based on Percentile
SHOW_STD_DEV = True  # sd = Show Standard Deviation Line

# ─────────────────────── INIT CLIENT ──────────────────────
client = api(api_key=API_KEY, host=API_HOST)


# ───────────────────── FETCH HISTORICAL DATA ─────────────────────
def fetch_historical_data():
    """Fetch 5m historical data for RELIANCE"""
    print(f"Fetching {SYMBOL} {INTERVAL} data from {START_DATE} to {END_DATE}...")

    response = client.history(
        symbol=SYMBOL,
        exchange=EXCHANGE,
        interval=INTERVAL,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    # Print the raw response
    print(f"History Response: {response}")

    # OpenAlgo history() returns DataFrame directly (not a dict)
    if isinstance(response, pd.DataFrame):
        df = response.copy()
    else:
        # Fallback if it returns dict
        df = pd.DataFrame(response.get("data", response))

    # Check if DataFrame is empty
    if df.empty:
        raise ValueError("No data received from API")

    # Handle index - if timestamp is already the index
    if df.index.name == "timestamp" or "timestamp" not in df.columns:
        df.index = pd.to_datetime(df.index)
    else:
        df["datetime"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("datetime")

    df = df.sort_index()

    # Standardize column names to lowercase
    df.columns = df.columns.str.lower()

    # Ensure we have OHLC columns
    required_cols = ["open", "high", "low", "close"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    print(f"Fetched {len(df)} candles")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    return df


# ───────────────────── WILLIAMS VIX FIX CALCULATION ─────────────────────
def calculate_williams_vix_fix(df: pd.DataFrame):
    """
    Calculate Williams Vix Fix indicator

    Formula from Pine Script:
    wvf = ((highest(close, pd) - low) / highest(close, pd)) * 100

    Then apply Bollinger Bands and Percentile Range to determine signals
    """

    close = df["close"]
    low = df["low"]

    # Calculate highest close over lookback period
    highest_close = ta.highest(close, WVF_LOOKBACK)

    # Williams Vix Fix formula
    # wvf = ((highest(close, pd) - low) / highest(close, pd)) * 100
    wvf = ((highest_close - low) / highest_close) * 100
    df["wvf"] = wvf

    # Bollinger Bands on WVF
    # midLine = sma(wvf, bbl)
    # sDev = mult * stdev(wvf, bbl)
    mid_line = ta.sma(wvf, BB_LENGTH)
    std_dev = ta.stdev(wvf, BB_LENGTH)
    s_dev = BB_MULT * std_dev

    df["wvf_midline"] = mid_line
    df["wvf_upper"] = mid_line + s_dev
    df["wvf_lower"] = mid_line - s_dev

    # Percentile Range
    # rangeHigh = (highest(wvf, lb)) * ph
    # rangeLow = (lowest(wvf, lb)) * pl
    range_high = ta.highest(wvf, PERCENTILE_LOOKBACK) * PERCENTILE_HIGH
    range_low = ta.lowest(wvf, PERCENTILE_LOOKBACK) * PERCENTILE_LOW

    df["range_high"] = range_high
    df["range_low"] = range_low

    # Color condition: Green (lime) when WVF >= upperBand OR WVF >= rangeHigh
    # col = wvf >= upperBand or wvf >= rangeHigh ? lime : gray
    df["wvf_signal"] = (wvf >= df["wvf_upper"]) | (wvf >= range_high)

    print(f"Calculated Williams Vix Fix (Lookback: {WVF_LOOKBACK}, BB: {BB_LENGTH}, {BB_MULT})")
    print(f"WVF Range: {wvf.min():.2f} to {wvf.max():.2f}")

    return df


# ───────────────────── PLOT CHART ─────────────────────
def plot_chart(df: pd.DataFrame):
    """Create interactive chart with Candlestick and Williams Vix Fix"""

    # Create x-axis as category strings (Plotly requirement)
    x_category = df.index.strftime("%d-%b<br>%H:%M").tolist()

    # Calculate tick positions (show ~15 labels for readability)
    total_candles = len(x_category)
    tick_step = max(1, total_candles // 15)
    tick_vals = [x_category[i] for i in range(0, total_candles, tick_step)]

    # Create subplots: Candlestick (top 70%), Williams Vix Fix (bottom 30%)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.70, 0.30],
        subplot_titles=[
            f"{SYMBOL} ({EXCHANGE}) - {INTERVAL}",
            f"Williams Vix Fix (pd={WVF_LOOKBACK}, bbl={BB_LENGTH}, mult={BB_MULT})",
        ],
    )

    # ───────── ROW 1: Candlestick ─────────
    fig.add_trace(
        go.Candlestick(
            x=x_category,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=SYMBOL,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    # ───────── ROW 2: Williams Vix Fix ─────────

    # Create color array based on signal condition
    colors = ["lime" if sig else "gray" for sig in df["wvf_signal"]]

    # WVF Histogram
    fig.add_trace(
        go.Bar(
            x=x_category, y=df["wvf"], name="Williams Vix Fix", marker_color=colors, showlegend=True
        ),
        row=2,
        col=1,
    )

    # Upper Band (Standard Deviation Line)
    if SHOW_STD_DEV:
        fig.add_trace(
            go.Scatter(
                x=x_category,
                y=df["wvf_upper"],
                name="Upper Band",
                line=dict(color="aqua", width=2),
                showlegend=True,
            ),
            row=2,
            col=1,
        )

    # Range High Percentile
    if SHOW_HIGH_RANGE:
        fig.add_trace(
            go.Scatter(
                x=x_category,
                y=df["range_high"],
                name=f"Range High ({PERCENTILE_HIGH * 100:.0f}%)",
                line=dict(color="orange", width=2, dash="dash"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=x_category,
                y=df["range_low"],
                name=f"Range Low ({(PERCENTILE_LOW - 1) * 100:.0f}%)",
                line=dict(color="orange", width=2, dash="dash"),
                showlegend=True,
            ),
            row=2,
            col=1,
        )

    # ───────── LAYOUT ─────────
    fig.update_layout(
        title=dict(
            text=f"{SYMBOL} with CM Williams Vix Fix<br><sup>{START_DATE} to {END_DATE}</sup>",
            x=0.5,
            font=dict(size=18),
        ),
        template="plotly_dark",
        height=900,
        width=1400,
        hovermode="x unified",
        margin=dict(l=60, r=100, t=80, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis2=dict(rangeslider=dict(visible=False)),
    )

    # Update x-axes
    fig.update_xaxes(
        type="category",
        tickmode="array",
        tickvals=tick_vals,
        tickangle=-45,
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        rangeslider=dict(visible=False),
        row=1,
        col=1,
    )

    fig.update_xaxes(
        type="category",
        tickmode="array",
        tickvals=tick_vals,
        tickangle=-45,
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        title="Date / Time",
        row=2,
        col=1,
    )

    # Update y-axes
    fig.update_yaxes(
        title="Price (₹)",
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        tickformat=",.2f",
        row=1,
        col=1,
    )

    fig.update_yaxes(title="WVF", showgrid=True, gridcolor="rgba(128, 128, 128, 0.2)", row=2, col=1)

    return fig


# ───────────────────── MAIN EXECUTION ─────────────────────
if __name__ == "__main__":
    try:
        # Fetch data
        df = fetch_historical_data()

        # Calculate Williams Vix Fix
        df = calculate_williams_vix_fix(df)

        # Create and display chart
        fig = plot_chart(df)

        # Save as HTML file
        output_file = "reliance_williams_vix_fix.html"
        fig.write_html(output_file)
        print(f"\nChart saved to: {output_file}")

        # Show the chart (opens in browser)
        fig.show()

    except Exception as e:
        print(f"Error: {e}")
        raise

```


---

# FILE: examples\python\ytd_gainers_losers.py

```py
# ---------------------------------------------------
# YTD 2026 Gainers & Losers for NIFTY 50
# Baseline: close on 2025-12-31 (last trading day of 2025)
# Data source: OpenAlgo Historify local DuckDB (source='db')
# ---------------------------------------------------

import pandas as pd
from openalgo import api

client = api(
    api_key="afd010bd748c9129d71901c53c1efb327c822fa5264e31959506d7aede79a336",
    host="http://127.0.0.1:5000",
)

SYMBOLS = [
    "INDIGO", "TRENT", "HINDUNILVR", "HCLTECH", "WIPRO", "INFY", "TATACONSUM",
    "TATASTEEL", "ITC", "ASIANPAINT", "SBILIFE", "LT", "SHRIRAMFIN", "BEL",
    "SBIN", "COALINDIA", "KOTAKBANK", "TCS", "SUNPHARMA", "MAXHEALTH",
    "NESTLEIND", "RELIANCE", "ETERNAL", "APOLLOHOSP", "ICICIBANK", "GRASIM",
    "ULTRACEMCO", "ADANIENT", "AXISBANK", "DRREDDY", "TECHM", "TMPV", "JIOFIN",
    "NTPC", "BAJFINANCE", "BHARTIARTL", "POWERGRID", "HINDALCO", "HDFCBANK",
    "TITAN", "HDFCLIFE", "MARUTI", "BAJAJFINSV", "ADANIPORTS", "CIPLA",
    "JSWSTEEL", "BAJAJ-AUTO", "ONGC", "EICHERMOT", "M&M",
]

BASELINE_DATE = pd.Timestamp("2025-12-31").date()
START_FETCH = "2025-12-30"
END_FETCH = "2026-12-31"

rows = []
missing = []
for sym in SYMBOLS:
    try:
        df = client.history(
            symbol=sym,
            exchange="NSE",
            interval="D",
            start_date=START_FETCH,
            end_date=END_FETCH,
            source="db",
        )
    except Exception as e:
        missing.append((sym, f"fetch error: {e}"))
        continue

    if not isinstance(df, pd.DataFrame) or df.empty:
        missing.append((sym, "no rows"))
        continue

    df = df.sort_index()
    df.index = pd.to_datetime(df.index).date

    if BASELINE_DATE not in df.index:
        missing.append((sym, f"no {BASELINE_DATE} close"))
        continue

    base = df.loc[BASELINE_DATE, "close"]
    last_date = df.index[-1]
    last_close = df.loc[last_date, "close"]
    if base <= 0:
        missing.append((sym, "non-positive base"))
        continue

    pct = ((last_close / base) - 1.0) * 100.0
    rows.append({
        "symbol": sym,
        "base_2025_12_31": round(float(base), 2),
        "last_close": round(float(last_close), 2),
        "last_date": last_date.isoformat(),
        "ytd_pct": round(float(pct), 2),
    })

if not rows:
    raise SystemExit("No data for any symbol. Run Historify bulk download first.")

df_all = pd.DataFrame(rows).sort_values("ytd_pct", ascending=False).reset_index(drop=True)
last_date_str = df_all["last_date"].iloc[0]

print(f"\n=== NIFTY 50 YTD 2026 (2025-12-31 close → {last_date_str}) ===\n")

print("TOP 10 GAINERS")
print(df_all.head(10).to_string(index=False))

print("\nTOP 10 LOSERS")
print(df_all.tail(10).iloc[::-1].to_string(index=False))

if missing:
    print(f"\nSkipped {len(missing)} symbols:")
    for sym, reason in missing:
        print(f"  {sym}: {reason}")

```


---

# FILE: examples\python\ytd_heatmap.py

```py
# ---------------------------------------------------
# NIFTY 50 YTD 2026 Heatmap
# Baseline: close on 2025-12-31 (last trading day of 2025)
# Sorted: top gainers top-left → top losers bottom-right
# Data source: OpenAlgo Historify local DuckDB (source='db')
# ---------------------------------------------------

import pandas as pd
import plotly.express as px
from openalgo import api

client = api(
    api_key="afd010bd748c9129d71901c53c1efb327c822fa5264e31959506d7aede79a336",
    host="http://127.0.0.1:5000",
)

SYMBOLS = [
    "INDIGO", "TRENT", "HINDUNILVR", "HCLTECH", "WIPRO", "INFY", "TATACONSUM",
    "TATASTEEL", "ITC", "ASIANPAINT", "SBILIFE", "LT", "SHRIRAMFIN", "BEL",
    "SBIN", "COALINDIA", "KOTAKBANK", "TCS", "SUNPHARMA", "MAXHEALTH",
    "NESTLEIND", "RELIANCE", "ETERNAL", "APOLLOHOSP", "ICICIBANK", "GRASIM",
    "ULTRACEMCO", "ADANIENT", "AXISBANK", "DRREDDY", "TECHM", "TMPV", "JIOFIN",
    "NTPC", "BAJFINANCE", "BHARTIARTL", "POWERGRID", "HINDALCO", "HDFCBANK",
    "TITAN", "HDFCLIFE", "MARUTI", "BAJAJFINSV", "ADANIPORTS", "CIPLA",
    "JSWSTEEL", "BAJAJ-AUTO", "ONGC", "EICHERMOT", "M&M",
]

BASELINE_DATE = pd.Timestamp("2025-12-31").date()

rows = []
last_date_str = None
for sym in SYMBOLS:
    try:
        df = client.history(
            symbol=sym,
            exchange="NSE",
            interval="D",
            start_date="2025-12-30",
            end_date="2026-12-31",
            source="db",
        )
    except Exception as e:
        print(f"{sym}: fetch error: {e}")
        continue

    if not isinstance(df, pd.DataFrame) or df.empty:
        print(f"{sym}: no rows")
        continue

    df = df.sort_index()
    df.index = pd.to_datetime(df.index).date

    if BASELINE_DATE not in df.index:
        print(f"{sym}: missing {BASELINE_DATE}")
        continue

    base = float(df.loc[BASELINE_DATE, "close"])
    last_close = float(df.iloc[-1]["close"])
    last_date_str = df.index[-1].isoformat()

    pct = ((last_close / base) - 1.0) * 100.0
    rows.append({"Symbol": sym, "Change": round(pct, 2)})

if not rows:
    raise SystemExit("No data. Run Historify bulk download first.")

df = pd.DataFrame(rows).sort_values("Change", ascending=False).reset_index(drop=True)

cols = 10
df["row"] = df.index // cols
df["col"] = df.index % cols

pivot_values = df.pivot(index="row", columns="col", values="Change")
pivot_labels = df.pivot(index="row", columns="col", values="Symbol")

fig = px.imshow(pivot_values, color_continuous_scale="RdYlGn", aspect="auto")
fig.update_traces(
    text=pivot_labels.values,
    texttemplate="%{text}<br>%{z:.2f}%",
    hovertemplate="Symbol: %{text}<br>YTD: %{z:.2f}%",
)
fig.update_layout(
    title="NIFTY 50 YTD 2026 Heatmap",
    xaxis=dict(showticklabels=False, title=""),
    yaxis=dict(showticklabels=False, autorange="reversed", title=""),
    template="plotly_dark",
    height=600,
)

out = "nifty50_ytd_heatmap.png"
fig.write_image(out, width=1200, height=600, scale=2)
print(f"\nSaved {out}  (as-of {last_date_str}, {len(df)} symbols)")

```

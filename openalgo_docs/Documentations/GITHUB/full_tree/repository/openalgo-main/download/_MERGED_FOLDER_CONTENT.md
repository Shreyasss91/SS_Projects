# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\download



---

# FILE: download\.sample.env

```env
API_KEY=your_openalgo_api_key
DB_NAME=amibroker.db
INTERVAL=1m
HOST=http://127.0.0.1:5000
MAX_REQUESTS_PER_SECOND=10
POLLING_INTERVAL_SECONDS=5
INITIAL_DAYS=30

```


---

# FILE: download\duckdb_downloader.py

```py

```


---

# FILE: download\ieod.py

```py
import gc
import logging
import os
import time
from datetime import datetime, timedelta

import pandas as pd
from openalgo import api

# Initialize the API client
client = api(api_key="your_api_key_here", host="http://127.0.0.1:5000")

# Path to the CSV file
symbols_file = "symbols.csv"
output_folder = "symbols"
checkpoint_file = "checkpoint.txt"

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename="data_download.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Function to get start date based on user selection
def get_date_range(option):
    today = datetime.now()
    if option == 1:
        return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif option == 2:
        return (today - timedelta(days=5)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif option == 3:
        return (today - timedelta(days=30)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif option == 4:
        return (today - timedelta(days=90)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif option == 5:
        return (today - timedelta(days=365)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif option == 6:
        return (today - timedelta(days=365 * 2)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif option == 7:
        return (today - timedelta(days=365 * 5)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    elif option == 8:
        return (today - timedelta(days=365 * 10)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    else:
        raise ValueError("Invalid selection")


# Prompt user for fresh download or continuation
print("Select download mode:")
print("1) Fresh download")
print("2) Continue from the last checkpoint")

try:
    mode_choice = int(input("Enter your choice (1-2): "))
    if mode_choice not in [1, 2]:
        raise ValueError("Invalid selection")
except ValueError:
    print("Invalid input. Please restart the script and select a valid option.")
    exit()

# Prompt user for time period
print("Select the time period for data download:")
print("1) Download Today's Data")
print("2) Download Last 5 Days Data")
print("3) Download Last 30 Days Data")
print("4) Download Last 90 Days Data")
print("5) Download Last 1 Year Data")
print("6) Download Last 2 Years Data")
print("7) Download Last 5 Years Data")
print("8) Download Last 10 Years Data")

try:
    user_choice = int(input("Enter your choice (1-8): "))
    start_date, end_date = get_date_range(user_choice)
except ValueError:
    print("Invalid input. Please restart the script and select a valid option.")
    exit()

# Read symbols from CSV
symbols = pd.read_csv(symbols_file, header=None)[0].tolist()

# Handle checkpoint logic
if mode_choice == 2 and os.path.exists(checkpoint_file):
    with open(checkpoint_file) as f:
        last_processed = f.read().strip()
    # Skip symbols up to the last processed one
    if last_processed in symbols:
        symbols = symbols[symbols.index(last_processed) + 1 :]
elif mode_choice == 1:
    # Remove existing checkpoint for fresh download
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

# Process symbols in batches
batch_size = 10  # Adjust this value based on your memory availability
for i in range(0, len(symbols), batch_size):
    batch = symbols[i : i + batch_size]
    for symbol in batch:
        logging.info(f"Starting download for {symbol}")
        try:
            # Skip already downloaded symbols
            output_file = os.path.join(output_folder, f"{symbol}.csv")
            if os.path.exists(output_file):
                logging.info(f"Skipping {symbol}, already downloaded")
                continue

            # Fetch historical data for the symbol
            for attempt in range(3):  # Retry up to 3 times
                try:
                    response = client.history(
                        symbol=symbol,
                        exchange="NSE",
                        interval="1m",
                        start_date=start_date,
                        end_date=end_date,
                    )
                    break
                except Exception as e:
                    logging.warning(f"Retry {attempt + 1} for {symbol} due to error: {e}")
                    time.sleep(5)  # Wait before retrying
            else:
                logging.error(f"Failed to download data for {symbol} after 3 attempts")
                continue

            # Convert the response to a DataFrame if it's a dictionary
            if isinstance(response, dict):
                if "timestamp" in response:
                    df = pd.DataFrame(response)
                else:
                    logging.error(f"Response for {symbol} missing 'timestamp' key: {response}")
                    continue
            else:
                df = response

            # Ensure the DataFrame is not empty
            if df.empty:
                logging.warning(f"No data available for {symbol}")
                continue

            # Reset the index to extract the timestamp
            df.reset_index(inplace=True)

            # Rename and split the timestamp column
            df["DATE"] = pd.to_datetime(df["timestamp"]).dt.date
            df["TIME"] = pd.to_datetime(df["timestamp"]).dt.time

            # Add SYMBOL column and rearrange columns
            df["SYMBOL"] = symbol
            df = df[["SYMBOL", "DATE", "TIME", "open", "high", "low", "close", "volume"]]
            df.columns = ["SYMBOL", "DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]

            # Save to CSV file
            df.to_csv(output_file, index=False)
            logging.info(f"Data for {symbol} saved to {output_file}")

            # Save checkpoint after successfully processing the symbol
            with open(checkpoint_file, "w") as f:
                f.write(symbol)

            # Clear DataFrame and force garbage collection
            del df
            gc.collect()

        except Exception as e:
            logging.error(f"Failed to download data for {symbol}: {e}")

        # Delay to avoid rate limiting
        time.sleep(3)

    logging.info(f"Batch of {batch_size} symbols completed.")

logging.info("All data downloaded.")

```


---

# FILE: download\README.md

```md
# IEOD Data Downloader

This tool allows you to download Intraday End of Day (IEOD) data for specified stock symbols from the OpenAlgo API.

## Prerequisites

- Python 3.x
- Valid OpenAlgo API key
- Access to OpenAlgo API endpoint (ensure openalgo is running)

## File Structure

- `ieod.py`: Main script for downloading IEOD data
- `symbols.csv`: List of stock symbols to download data for
- `checkpoint.txt`: Tracks download progress (automatically created)
- `data_download.log`: Log file for download operations (automatically created)

## Setup

1. Ensure you have a valid API key from OpenAlgo
2. Place your stock symbols in `symbols.csv` (one symbol per line)
3. The script will automatically create necessary folders and files

## Usage

Run the script using Python:

```bash
python ieod.py
```

### Download Options

The script provides two modes of operation:

1. Fresh Download
2. Continue from Last Checkpoint

### Time Period Options

You can select from various time periods for data download:

1. Today's Data
2. Last 5 Days Data
3. Last 30 Days Data
4. Last 90 Days Data
5. Last 1 Year Data
6. Last 2 Years Data
7. Last 5 Years Data
8. Last 10 Years Data

### Output

- Downloaded data is saved in the `symbols` folder
- Each symbol's data is saved in a separate CSV file
- Progress is tracked in `checkpoint.txt`
- Download logs are saved in `data_download.log`

## symbols.csv Format

The `symbols.csv` file should contain one stock symbol per line. Example:

```
RELIANCE
ICICIBANK
HDFCBANK
SBIN
TCS
INFY
```

## Error Handling

- The script includes error handling and logging
- Failed downloads are logged in `data_download.log`
- The checkpoint system allows resuming interrupted downloads

## Notes

- Data is downloaded in batches to manage memory efficiently
- Default batch size is 10 symbols (adjustable in the code)
- The script includes rate limiting to prevent API overload

```


---

# FILE: download\sqlite_downloader.py

```py
import json
import os
import time
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv
from openalgo import api
from sqlalchemy import MetaData, create_engine

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
DB_NAME = os.getenv("DB_NAME", "amibroker.db")
INTERVAL = os.getenv("INTERVAL", "1m")
HOST = os.getenv("HOST", "http://127.0.0.1:5000")
MAX_RPS = int(os.getenv("MAX_REQUESTS_PER_SECOND", 10))
POLL_INTERVAL = int(os.getenv("POLLING_INTERVAL_SECONDS", 5))
INITIAL_DAYS = int(os.getenv("INITIAL_DAYS", 30))

# Paths
DB_FOLDER = os.path.join("..", "db")
os.makedirs(DB_FOLDER, exist_ok=True)

DB_PATH = os.path.join(DB_FOLDER, DB_NAME)
CHECKPOINT_FILE = os.path.join(DB_FOLDER, "checkpoints.json")

# Setup
client = api(api_key=API_KEY, host=HOST)
engine = create_engine(f"sqlite:///{DB_PATH}")
metadata = MetaData()
metadata.reflect(bind=engine)

# Load checkpoints
if os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE) as f:
        checkpoints = json.load(f)
else:
    checkpoints = {}


def save_checkpoints():
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoints, f, indent=2)


def get_symbols():
    if not os.path.exists("symbols.csv"):
        return []
    df = pd.read_csv("symbols.csv", header=None)
    return df[0].dropna().astype(str).str.strip().tolist()


def fetch_and_store(symbol):
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = checkpoints.get(
        symbol, (datetime.now() - pd.Timedelta(days=INITIAL_DAYS)).strftime("%Y-%m-%d")
    )
    end_date = today

    response = client.history(
        symbol=symbol, exchange="NSE", interval=INTERVAL, start_date=start_date, end_date=end_date
    )

    if not isinstance(response, pd.DataFrame) or response.empty:
        print(f"[{symbol}] No data returned or invalid response.")
        return

    df = response
    df.index = pd.to_datetime(df.index)
    df = df[df.index.strftime("%Y-%m-%d") >= start_date]

    if df.empty:
        print(f"[{symbol}] No new rows after filtering.")
        return

    # Convert timestamps from UTC to IST (subtract 5:30 hours)
    ist_timestamps = df.index - timedelta(hours=5, minutes=30)

    df["SYMBOL"] = symbol
    df["DATE"] = ist_timestamps.strftime("%Y-%m-%d %H:%M:%S")
    df = df[["SYMBOL", "DATE", "open", "high", "low", "close", "volume"]]
    df.columns = ["SYMBOL", "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]

    df.to_sql("stock_data", con=engine, if_exists="append", index=False)

    last_dt = df.index.max().strftime("%Y-%m-%d")
    checkpoints[symbol] = last_dt
    print(f"[{symbol}] Inserted {len(df)} records. Updated checkpoint: {last_dt}")


# Main loop with throttling
while True:
    try:
        symbols = get_symbols()
        for i, symbol in enumerate(symbols):
            fetch_and_store(symbol)
            if (i + 1) % MAX_RPS == 0:
                print("Rate limit reached. Sleeping 1s...")
                time.sleep(1)
        save_checkpoints()
        time.sleep(POLL_INTERVAL)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(POLL_INTERVAL)

```


---

# FILE: download\symbols.csv

```csv
RELIANCE
ICICIBANK
HDFCBANK
SBIN
TCS
INFY
```

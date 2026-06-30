# OpenAlgo SDK Holiday API Binding

The OpenAlgo Python SDK provides a `holidays()` method to retrieve exchange holidays, settlement holidays, and partial trading session information for a given year. :contentReference[oaicite:0]{index=0}

## SDK Initialization

```python
import os
from openalgo import api

api_key = os.getenv("OPENALGO_API_KEY")

host = (
    os.getenv("HOST_SERVER")
    or os.getenv("OPENALGO_HOST")
    or "http://127.0.0.1:5000"
)

client = api(
    api_key=api_key,
    host=host
)

print("🔁 OpenAlgo Python Bot is running.")
```

---

## Get Holidays for a Year

```python
response = client.holidays(year=2026)

print(response)
```

---

## Example Response

```json
{
  "status": "success",
  "data": [
    {
      "date": "2026-01-26",
      "description": "Republic Day",
      "holiday_type": "TRADING_HOLIDAY",
      "closed_exchanges": [
        "NSE",
        "BSE",
        "NFO",
        "BFO",
        "CDS",
        "BCD",
        "MCX"
      ],
      "open_exchanges": []
    },
    {
      "date": "2026-02-19",
      "description": "Chhatrapati Shivaji Maharaj Jayanti",
      "holiday_type": "SETTLEMENT_HOLIDAY",
      "closed_exchanges": [],
      "open_exchanges": []
    }
  ]
}
```
:contentReference[oaicite:1]{index=1}

---

## Print All Trading Holidays

```python
response = client.holidays(year=2026)

if response.get("status") == "success":

    for holiday in response["data"]:

        if holiday["holiday_type"] == "TRADING_HOLIDAY":

            print(
                f"{holiday['date']} | "
                f"{holiday['description']} | "
                f"{holiday['holiday_type']}"
            )
```

---

## Filter Holidays for NSE

```python
response = client.holidays(year=2026)

if response.get("status") == "success":

    nse_holidays = [
        h for h in response["data"]
        if "NSE" in h.get("closed_exchanges", [])
    ]

    for holiday in nse_holidays:
        print(
            holiday["date"],
            holiday["description"]
        )
```

---

## Check if a Specific Date is a Trading Holiday

```python
check_date = "2026-01-26"

response = client.holidays(year=2026)

is_holiday = False

if response.get("status") == "success":

    for holiday in response["data"]:

        if (
            holiday["date"] == check_date
            and holiday["holiday_type"] == "TRADING_HOLIDAY"
        ):
            is_holiday = True
            print(
                f"{check_date} is a trading holiday: "
                f"{holiday['description']}"
            )
            break

if not is_holiday:
    print(f"{check_date} is a trading day.")
```

---

## Get MCX Partial Trading Sessions

Some holidays may keep MCX open for an evening session. The API exposes these sessions through the `open_exchanges` field. :contentReference[oaicite:2]{index=2}

```python
response = client.holidays(year=2026)

if response.get("status") == "success":

    for holiday in response["data"]:

        if holiday.get("open_exchanges"):

            print(
                holiday["date"],
                holiday["description"]
            )

            for session in holiday["open_exchanges"]:

                print(
                    session["exchange"],
                    session["start_time"],
                    session["end_time"]
                )
```

---

## Recommended Safety Helper

```python
def is_exchange_holiday(client, date_str, exchange):
    response = client.holidays(year=int(date_str[:4]))

    if response.get("status") != "success":
        return False

    for holiday in response["data"]:

        if (
            holiday["date"] == date_str
            and exchange in holiday.get("closed_exchanges", [])
        ):
            return True

    return False


print(
    is_exchange_holiday(
        client,
        "2026-01-26",
        "NSE"
    )
)
```

---

## Method Signature

```python
response = client.holidays(
    year=2026
)
```

### Parameters

| Parameter | Type | Required | Description |
|------------|------|----------|-------------|
| year | int | Yes | Holiday calendar year |

### Returns

```python
{
    "status": "success",
    "data": [...]
}
```

Reference: OpenAlgo Holidays API (`client.holidays(year=YYYY)`). :contentReference[oaicite:3]{index=3}
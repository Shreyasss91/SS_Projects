import os
from pprint import pprint
from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

api_key = os.getenv("OPENALGO_API_KEY")
host = os.getenv("HOST_SERVER") or os.getenv("OPENALGO_HOST") or "http://127.0.0.1:5000"

client = api(
    api_key=api_key,
    host=host
)

# --------------------------------------------------
# EXPIRY
# --------------------------------------------------

exp = client.expiry(
    symbol="NIFTY",
    exchange="NFO",
    instrumenttype="options"
)

expiry = exp["data"][0]
expiry = expiry.replace("-", "")

print("\nUsing Expiry:", expiry)

# --------------------------------------------------
# OPTIONCHAIN
# --------------------------------------------------

chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date=expiry,
    strike_count=3
)

print("\n================ OPTIONCHAIN ================")

atm = chain["atm_strike"]

print("ATM:", atm)

row = chain["chain"][1]   # ATM row

print("\nCE KEYS")
print(sorted(row["ce"].keys()))

print("\nPE KEYS")
print(sorted(row["pe"].keys()))

print("\nATM CE DATA")
pprint(row["ce"])

print("\nATM PE DATA")
pprint(row["pe"])

print(
    "\nOPTIONCHAIN VOLUME CHECK",
    "\nCE Volume =", row["ce"].get("volume"),
    "\nPE Volume =", row["pe"].get("volume")
)

# --------------------------------------------------
# MULTIQUOTES
# --------------------------------------------------

ce_symbol = row["ce"]["symbol"]
pe_symbol = row["pe"]["symbol"]

mq = client.multiquotes(
    symbols=[
        {
            "symbol": ce_symbol,
            "exchange": "NFO"
        },
        {
            "symbol": pe_symbol,
            "exchange": "NFO"
        }
    ]
)

print("\n================ MULTIQUOTES ================")

for item in mq["results"]:

    print("\n------------------------------------")
    print(item["symbol"])

    print("\nKEYS")
    print(sorted(item["data"].keys()))

    print("\nFULL DATA")
    pprint(item["data"])

    print(
        "\nVOLUME =",
        item["data"].get("volume")
    )

    print(
        "OI =",
        item["data"].get("oi")
    )
    
    
print("\n================================")
print("\nRaw response of client.optionchain")
print(chain)

print("\n================================")
print("\nRaw response of client.multiquotes")
print(mq)


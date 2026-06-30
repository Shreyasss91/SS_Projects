import os
from openalgo import api

print("🔁 OpenAlgo Python Bot is running.")

api_key = os.getenv("OPENALGO_API_KEY")
host = os.getenv("HOST_SERVER") or os.getenv("OPENALGO_HOST") or "http://127.0.0.1:5000"

client = api(api_key=api_key, host=host)

for m in sorted(dir(client)):
    if not m.startswith("_"):
        print(m)


obj = getattr(client, "splitorder")
print(type(obj))
print(callable(obj))
print(repr(obj))
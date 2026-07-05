import requests

url = "http://100.108.179.50:5000"

try:
    r = requests.get(url, timeout=5)
    print("SUCCESS")
    print("Status:", r.status_code)
except Exception as e:
    print("FAILED")
    print(e)
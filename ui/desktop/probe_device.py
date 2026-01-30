import requests
import json

IP = "192.168.31.142"
BASE_URL = f"http://{IP}"

endpoints = [
    "/status",
    "/on",
    "/off",
    "/power?state=on",
    "/power?state=off",
    "/color?r=255&g=0&b=0"
]

print(f"Probing {BASE_URL}...")

for ep in endpoints:
    url = f"{BASE_URL}{ep}"
    print(f"\nScanning: {url}")
    try:
        resp = requests.get(url, timeout=3)
        print(f"Status: {resp.status_code}")
        print(f"Content: {resp.text}")
        if resp.headers.get("Content-Type") == "application/json":
            try:
                print("JSON Decode: OK")
                print(resp.json())
            except:
                print("JSON Decode: FAIL")
    except Exception as e:
        print(f"Error: {e}")

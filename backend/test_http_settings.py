import requests

print("Testando endpoint /settings...")
try:
    r = requests.get("http://localhost:8000/settings")
    print(f"STATUS: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"company_name: {data.get('company_name')}")
        print(f"trade_name: {data.get('trade_name')}")
        print(f"city: {data.get('city')}")
        print(f"state: {data.get('state')}")
    else:
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

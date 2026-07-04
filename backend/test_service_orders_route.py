"""Testa a rota de service orders"""
import requests

# 1. Login para obter token
login_url = "http://localhost:8000/auth/login"
login_data = {
    "username": "admin@jsp.com",
    "password": "123456"
}

print("Fazendo login...")
login_response = requests.post(login_url, data=login_data)

if login_response.status_code != 200:
    print(f"ERRO no login: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print("Token obtido!")

# 2. Testar rota de service orders
print("\nTestando GET /service-orders...")
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/service-orders?page=1&page_size=15",
    headers=headers
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"SUCCESS! Retornados {len(data.get('items', []))} items")
    print(f"Total: {data.get('total', 0)}")
else:
    print(f"ERRO: {response.text[:500]}")


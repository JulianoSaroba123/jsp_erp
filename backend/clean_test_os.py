"""Limpa OSs de teste do banco de dados."""
import requests

API_BASE = "http://localhost:8000"
ADMIN_EMAIL = "admin@jsp.com"
ADMIN_PASSWORD = "admin123"

print("Fazendo login...")
login_response = requests.post(
    f"{API_BASE}/auth/login",
    data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30
)

if login_response.status_code != 200:
    print(f"Erro no login: {login_response.status_code}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Buscando OSs de teste...")
search_response = requests.get(
    f"{API_BASE}/service-orders",
    headers=headers,
    params={"page": 1, "page_size": 100},
    timeout=30
)

if search_response.status_code != 200:
    print(f"Erro ao buscar OSs: {search_response.status_code}")
    exit(1)

orders = search_response.json().get("items", [])
test_orders = [o for o in orders if "TESTE" in o.get("title", "").upper() or "Preservação" in o.get("title", "")]

print(f"Encontradas {len(test_orders)} OSs de teste")

for order in test_orders:
    print(f"Deletando OS {order['number']} - {order['title']}")
    delete_response = requests.delete(
        f"{API_BASE}/service-orders/{order['id']}",
        headers=headers,
        timeout=30
    )
    if delete_response.status_code == 204:
        print(f"  ✅ Deletada")
    else:
        print(f"  ❌ Erro: {delete_response.status_code}")

print("Limpeza concluída!")

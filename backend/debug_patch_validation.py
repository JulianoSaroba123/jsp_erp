"""
Script para testar PATCH com debug completo de validação.
Mostra exatamente qual campo está causando o erro 422.
"""
import requests
import sys
from pprint import pprint

API_BASE = "http://localhost:8000"
ADMIN_EMAIL = "admin@jsp.com"
ADMIN_PASSWORD = "admin123"

print("=" * 80)
print("DEBUG: PATCH SERVICE ORDER COM VALIDAÇÃO DETALHADA")
print("=" * 80)

# Login
print("\n1. Login...")
login_response = requests.post(
    f"{API_BASE}/auth/login",
    data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login OK")

# Buscar uma OS existente
print("\n2. Buscando OS existente...")
list_response = requests.get(
    f"{API_BASE}/service-orders",
    headers=headers,
    params={"page": 1, "page_size": 1}
)

if not list_response.json()["items"]:
    print("❌ Nenhuma OS encontrada no banco!")
    sys.exit(1)

os_data = list_response.json()["items"][0]
os_id = os_data["id"]
os_number = os_data["number"]

print(f"✅ OS encontrada: {os_number}")
print(f"   ID: {os_id}")
print(f"   Título: {os_data['title']}")
print(f"   Status: {os_data['status']}")

# Tentar update simples
print("\n3. Tentando PATCH simples (só título)...")
simple_payload = {
    "title": "Teste Update Simples"
}

simple_response = requests.patch(
    f"{API_BASE}/service-orders/{os_id}",
    json=simple_payload,
    headers=headers
)

print(f"   Status: {simple_response.status_code}")
if simple_response.status_code == 200:
    print("   ✅ Update simples funcionou!")
else:
    print(f"   ❌ Erro: {simple_response.text}")

# Tentar update complexo (como o frontend enviaria)
print("\n4. Tentando PATCH complexo (múltiplos campos)...")
complex_payload = {
    "customer_id": os_data["customer_id"],
    "order_type": os_data["order_type"],
    "title": "Teste Update Complexo",
    "description": "Descrição atualizada",
    "status": os_data["status"],
    "priority": "alta",
    "equipment": "Equipamento Atualizado",
    "total_amount": 500.00
}

complex_response = requests.patch(
    f"{API_BASE}/service-orders/{os_id}",
    json=complex_payload,
    headers=headers
)

print(f"   Status: {complex_response.status_code}")
if complex_response.status_code == 200:
    print("   ✅ Update complexo funcionou!")
else:
    print(f"   ❌ Erro no update complexo:")
    print(f"\n{complex_response.text}\n")

# Tentar com items/products (erro esperado no frontend antigo)
print("\n5. Tentando PATCH com items/products (como frontend antigo enviava)...")
with_items_payload = {
    "title": "Teste com Items",
    "items": [
        {"description": "Serviço 1", "quantity": 1, "unit_price": 100, "total_price": 100}
    ],
    "products": []
}

with_items_response = requests.patch(
    f"{API_BASE}/service-orders/{os_id}",
    json=with_items_payload,
    headers=headers
)

print(f"   Status: {with_items_response.status_code}")
if with_items_response.status_code == 200:
    print("   ✅ Backend aceitou payload com items (service layer removeu)")
else:
    print(f"   ❌ Erro:")
    print(f"\n{with_items_response.text}\n")

print("\n" + "=" * 80)
print("RESULTADO DO DEBUG")
print("=" * 80)
print(f"Update simples: {'✅' if simple_response.status_code == 200 else '❌'}")
print(f"Update complexo: {'✅' if complex_response.status_code == 200 else '❌'}")
print(f"Update com items: {'✅' if with_items_response.status_code == 200 else '❌'}")
print("=" * 80)

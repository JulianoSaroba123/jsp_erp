"""
Teste automatizado para edição (UPDATE/PATCH) de Ordem de Serviço.

Testa:
1. Criação de uma OS de teste
2. PATCH para atualizar campos da OS
3. Verificação dos campos atualizados
4. Cleanup dos dados de teste
"""
import requests
import sys
from datetime import date, timedelta

API_BASE = "http://localhost:8000"

# Credenciais de admin
ADMIN_EMAIL = "admin@jsp.com"
ADMIN_PASSWORD = "admin123"

print("=" * 80)
print("TESTE DE EDIÇÃO/UPDATE DE ORDEM DE SERVIÇO - ERP JSP")
print("=" * 80)

# ==================== 1. LOGIN ====================
print("\n1️⃣ Fazendo login...")

try:
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=5
    )
    
    if login_response.status_code != 200:
        print(f"   ❌ Erro no login: {login_response.status_code}")
        print(f"   Resposta: {login_response.text}")
        sys.exit(1)
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("   ✅ Login realizado com sucesso!")

except requests.exceptions.ConnectionError:
    print("   ❌ ERRO: Backend não está rodando!")
    print("   Execute: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    sys.exit(1)

# ==================== 2. BUSCAR CLIENTE ====================
print("\n2️⃣ Buscando cliente para teste...")

customers_response = requests.get(
    f"{API_BASE}/customers",
    headers=headers,
    params={"page": 1, "page_size": 1},
    timeout=5
)

if customers_response.status_code != 200 or not customers_response.json()["items"]:
    print("   ❌ Nenhum cliente encontrado no banco!")
    sys.exit(1)

customer_id = customers_response.json()["items"][0]["id"]
customer_name = customers_response.json()["items"][0]["name"]

print(f"   ✅ Cliente encontrado: {customer_name} ({customer_id})")

# ==================== 3. CRIAR OS DE TESTE ====================
print("\n3️⃣ Criando Ordem de Serviço de teste...")

create_payload = {
    "customer_id": customer_id,
    "order_type": "comercial",
    "title": "OS de Teste - Edição Automatizada",
    "description": "Teste automatizado de edição de OS",
    "priority": "normal",
    "status": "pendente",
    "expected_date": (date.today() + timedelta(days=7)).isoformat(),
    "equipment": "Equipamento Original",
    "total_amount": 100.00,
    "warranty_days": 30
}

create_response = requests.post(
    f"{API_BASE}/service-orders",
    json=create_payload,
    headers=headers,
    timeout=5
)

if create_response.status_code != 201:
    print(f"   ❌ Erro ao criar OS: {create_response.status_code}")
    print(f"   Resposta: {create_response.text}")
    sys.exit(1)

os_data = create_response.json()
os_id = os_data["id"]
os_number = os_data["number"]

print(f"   ✅ OS criada: {os_number} (ID: {os_id})")
print(f"      - Título: {os_data['title']}")
print(f"      - Prioridade: {os_data['priority']}")
print(f"      - Equipamento: {os_data['equipment']}")
print(f"      - Valor: R$ {os_data['total_amount']}")

# ==================== 4. ATUALIZAR OS (PATCH) ====================
print("\n4️⃣ Atualizando OS via PATCH...")

update_payload = {
    "title": "OS de Teste - ATUALIZADA",
    "description": "Descrição foi atualizada com sucesso",
    "priority": "alta",
    "equipment": "Equipamento ATUALIZADO",
    "brand_model": "Marca/Modelo Atualizado",
    "serial_number": "SN-12345-UPDATED",
    "total_amount": 250.00,
    "warranty_days": 90,
    "notes": "Observações adicionadas via update"
}

update_response = requests.patch(
    f"{API_BASE}/service-orders/{os_id}",
    json=update_payload,
    headers=headers,
    timeout=5
)

if update_response.status_code != 200:
    print(f"   ❌ Erro ao atualizar OS: {update_response.status_code}")
    print(f"   Resposta: {update_response.text}")
    
    # Tentar cleanup antes de sair
    requests.delete(f"{API_BASE}/service-orders/{os_id}", headers=headers)
    sys.exit(1)

updated_os = update_response.json()

print("   ✅ OS atualizada com sucesso!")
print(f"      - Título: {updated_os['title']} {'✅' if updated_os['title'] == update_payload['title'] else '❌'}")
print(f"      - Descrição: {updated_os['description']} {'✅' if updated_os['description'] == update_payload['description'] else '❌'}")
print(f"      - Prioridade: {updated_os['priority']} {'✅' if updated_os['priority'] == update_payload['priority'] else '❌'}")
print(f"      - Equipamento: {updated_os['equipment']} {'✅' if updated_os['equipment'] == update_payload['equipment'] else '❌'}")
print(f"      - Marca/Modelo: {updated_os['brand_model']} {'✅' if updated_os['brand_model'] == update_payload['brand_model'] else '❌'}")
print(f"      - Serial: {updated_os['serial_number']} {'✅' if updated_os['serial_number'] == update_payload['serial_number'] else '❌'}")
print(f"      - Valor: R$ {updated_os['total_amount']} {'✅' if float(updated_os['total_amount']) == update_payload['total_amount'] else '❌'}")
print(f"      - Garantia: {updated_os['warranty_days']} dias {'✅' if updated_os['warranty_days'] == update_payload['warranty_days'] else '❌'}")
print(f"      - Notas: {updated_os['notes']} {'✅' if updated_os['notes'] == update_payload['notes'] else '❌'}")

# ==================== 5. VERIFICAR CAMPOS ====================
print("\n5️⃣ Verificando campos atualizados...")

errors = []

if updated_os['title'] != update_payload['title']:
    errors.append(f"❌ Título incorreto: esperado '{update_payload['title']}', obtido '{updated_os['title']}'")

if updated_os['description'] != update_payload['description']:
    errors.append(f"❌ Descrição incorreta: esperado '{update_payload['description']}', obtido '{updated_os['description']}'")

if updated_os['priority'] != update_payload['priority']:
    errors.append(f"❌ Prioridade incorreta: esperado '{update_payload['priority']}', obtido '{updated_os['priority']}'")

if updated_os['equipment'] != update_payload['equipment']:
    errors.append(f"❌ Equipamento incorreto: esperado '{update_payload['equipment']}', obtido '{updated_os['equipment']}'")

if float(updated_os['total_amount']) != update_payload['total_amount']:
    errors.append(f"❌ Valor incorreto: esperado {update_payload['total_amount']}, obtido {updated_os['total_amount']}")

if updated_os['warranty_days'] != update_payload['warranty_days']:
    errors.append(f"❌ Garantia incorreta: esperado {update_payload['warranty_days']}, obtido {updated_os['warranty_days']}")

if errors:
    print("   ⚠️ Alguns campos não foram atualizados corretamente:")
    for error in errors:
        print(f"      {error}")
else:
    print("   ✅ Todos os campos foram atualizados corretamente!")

# ==================== 6. CLEANUP ====================
print("\n6️⃣ Removendo OS de teste...")

delete_response = requests.delete(
    f"{API_BASE}/service-orders/{os_id}",
    headers=headers,
    timeout=5
)

if delete_response.status_code == 204:
    print("   ✅ OS de teste removida com sucesso!")
else:
    print(f"   ⚠️ Não foi possível remover a OS: {delete_response.status_code}")

# ==================== RESULTADO FINAL ====================
print("\n" + "=" * 80)
if errors:
    print("⚠️ TESTE CONCLUÍDO COM RESSALVAS")
    print("=" * 80)
    print(f"OS foi atualizada, mas {len(errors)} campo(s) apresentaram inconsistências.")
else:
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    print("A edição/update de Ordem de Serviço está funcionando corretamente.")
print("=" * 80)

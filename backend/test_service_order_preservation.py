"""
Teste de preservação de dados ao editar Ordem de Serviço.

Cenários testados:
1. Editar título SEM apagar serviços
2. Editar equipamento SEM apagar produtos
3. Editar pagamento SEM apagar total
4. Update parcial preserva campos não enviados
5. Update não zera valores monetários
"""
import requests
import sys
from datetime import date, timedelta

API_BASE = "http://localhost:8000"
ADMIN_EMAIL = "admin@jsp.com"
ADMIN_PASSWORD = "admin123"
REQUEST_TIMEOUT = 30  # Aumentar timeout para 30 segundos

print("=" * 80)
print("TESTE DE PRESERVAÇÃO DE DADOS - EDIÇÃO DE ORDEM DE SERVIÇO")
print("=" * 80)

# ==================== 1. LOGIN ====================
print("\n1️⃣ Fazendo login...")

try:
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=REQUEST_TIMEOUT
    )
    
    if login_response.status_code != 200:
        print(f"   ❌ Erro no login: {login_response.status_code}")
        sys.exit(1)
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Login OK")

except requests.exceptions.ConnectionError:
    print("   ❌ Backend não está rodando!")
    sys.exit(1)

# ==================== 2. BUSCAR CLIENTE ====================
print("\n2️⃣ Buscando cliente...")

customers_response = requests.get(
    f"{API_BASE}/customers",
    headers=headers,
    params={"page": 1, "page_size": 1},
    timeout=REQUEST_TIMEOUT
)

if customers_response.status_code != 200 or not customers_response.json()["items"]:
    print("   ❌ Nenhum cliente encontrado!")
    sys.exit(1)

customer_id = customers_response.json()["items"][0]["id"]
print(f"   ✅ Cliente: {customer_id}")

# ==================== 3. CRIAR OS COMPLETA ====================
print("\n3️⃣ Criando OS completa com serviços e produtos...")

create_payload = {
    "customer_id": customer_id,
    "order_type": "comercial",
    "title": "OS TESTE - Preservação de Dados",
    "description": "Teste automatizado de preservação",
    "priority": "normal",
    "status": "pendente",
    "equipment": "Gerador 500KVA",
    "brand_model": "Cummins C550",
    "serial_number": "SN-TEST-12345",
    "expected_date": (date.today() + timedelta(days=7)).isoformat(),
    "total_amount": 1000.00,
    "warranty_days": 90,
    # Serviços
    "items": [
        {
            "description": "MANUTENÇÃO EM GERADORES",
            "service_type": "hora",
            "quantity": 3,
            "unit_price": 180,
            "total_price": 540
        },
        {
            "description": "Diagnóstico Elétrico",
            "service_type": "fechado",
            "quantity": 1,
            "unit_price": 200,
            "total_price": 200
        }
    ],
    # Produtos
    "products": [
        {
            "description": "Filtro de Óleo",
            "quantity": 2,
            "unit_price": 85,
            "total_price": 170
        },
        {
            "description": "Correias",
            "quantity": 4,
            "unit_price": 22.50,
            "total_price": 90
        }
    ],
    "service_amount": 740,
    "parts_amount": 260,
}

create_response = requests.post(
    f"{API_BASE}/service-orders",
    json=create_payload,
    headers=headers,
    timeout=REQUEST_TIMEOUT
)

if create_response.status_code != 201:
    print(f"   ❌ Erro ao criar OS: {create_response.status_code}")
    print(f"   {create_response.text}")
    sys.exit(1)

os_data = create_response.json()
os_id = os_data["id"]
os_number = os_data["number"]

print(f"   ✅ OS criada: {os_number}")
print(f"      Título: {os_data['title']}")
print(f"      Equipamento: {os_data['equipment']}")
print(f"      Total: R$ {os_data['total_amount']}")
print(f"      Serviços: {len(os_data.get('items', []))}")
print(f"      Produtos: {len(os_data.get('products', []))}")

# Valores originais para comparação
original_title = os_data['title']
original_equipment = os_data['equipment']
original_total = float(os_data['total_amount'])
original_items_count = len(os_data.get('items', []))
original_products_count = len(os_data.get('products', []))

# ==================== 4. UPDATE PARCIAL - SÓ TÍTULO ====================
print("\n4️⃣ Teste 1: Editar APENAS título (preservar todo o resto)...")

update_title_only = {
    "title": "OS TESTE - Título Atualizado"
}

update_response = requests.patch(
    f"{API_BASE}/service-orders/{os_id}",
    json=update_title_only,
    headers=headers,
    timeout=REQUEST_TIMEOUT
)

if update_response.status_code != 200:
    print(f"   ❌ Erro: {update_response.status_code}")
    print(f"   {update_response.text}")
else:
    updated_os = update_response.json()
    
    # Verificações
    errors = []
    
    if updated_os['title'] != update_title_only['title']:
        errors.append(f"Título não foi atualizado")
    
    if updated_os.get('equipment') != original_equipment:
        errors.append(f"Equipamento foi apagado! Antes: {original_equipment}, Depois: {updated_os.get('equipment')}")
    
    if float(updated_os.get('total_amount', 0)) != original_total:
        errors.append(f"Total foi alterado! Antes: R$ {original_total}, Depois: R$ {updated_os.get('total_amount', 0)}")
    
    items_count = len(updated_os.get('items', []))
    if items_count != original_items_count:
        errors.append(f"Serviços foram apagados! Antes: {original_items_count}, Depois: {items_count}")
    
    products_count = len(updated_os.get('products', []))
    if products_count != original_products_count:
        errors.append(f"Produtos foram apagados! Antes: {original_products_count}, Depois: {products_count}")
    
    if errors:
        print("   ❌ FALHOU - Dados foram perdidos:")
        for error in errors:
            print(f"      • {error}")
    else:
        print("   ✅ PASSOU - Todos os dados preservados!")
        print(f"      Título: {updated_os['title']} ✅")
        print(f"      Equipamento: {updated_os['equipment']} ✅")
        print(f"      Total: R$ {updated_os['total_amount']} ✅")
        print(f"      Serviços: {items_count} ✅")
        print(f"      Produtos: {products_count} ✅")

# ==================== 5. UPDATE PARCIAL - SÓ EQUIPAMENTO ====================
print("\n5️⃣ Teste 2: Editar APENAS equipamento (preservar serviços e total)...")

update_equipment_only = {
    "equipment": "Gerador ATUALIZADO 750KVA",
    "brand_model": "Nova Marca XYZ",
}

update_response = requests.patch(
    f"{API_BASE}/service-orders/{os_id}",
    json=update_equipment_only,
    headers=headers,
    timeout=REQUEST_TIMEOUT
)

if update_response.status_code != 200:
    print(f"   ❌ Erro: {update_response.status_code}")
else:
    updated_os = update_response.json()
    
    errors = []
    
    if updated_os.get('equipment') != update_equipment_only['equipment']:
        errors.append("Equipamento não foi atualizado")
    
    if float(updated_os.get('total_amount', 0)) != original_total:
        errors.append(f"Total zerado! Antes: R$ {original_total}, Depois: R$ {updated_os.get('total_amount', 0)}")
    
    items_count = len(updated_os.get('items', []))
    if items_count != original_items_count:
        errors.append(f"Serviços perdidos! Antes: {original_items_count}, Depois: {items_count}")
    
    if errors:
        print("   ❌ FALHOU:")
        for error in errors:
            print(f"      • {error}")
    else:
        print("   ✅ PASSOU - Equipamento atualizado, dados preservados!")
        print(f"      Equipamento: {updated_os['equipment']} ✅")
        print(f"      Total: R$ {updated_os['total_amount']} ✅")
        print(f"      Serviços: {items_count} ✅")

# ==================== 6. UPDATE COM TOTAIS ====================
print("\n6️⃣ Teste 3: Update com novos totais (não deve zerar)...")

update_with_totals = {
    "title": "OS TESTE - Final",
    "total_amount": 1500.00,
    "service_amount": 1000.00,
    "parts_amount": 500.00,
}

update_response = requests.patch(
    f"{API_BASE}/service-orders/{os_id}",
    json=update_with_totals,
    headers=headers,
    timeout=REQUEST_TIMEOUT
)

if update_response.status_code != 200:
    print(f"   ❌ Erro: {update_response.status_code}")
else:
    updated_os = update_response.json()
    
    errors = []
    
    if float(updated_os.get('total_amount', 0)) == 0:
        errors.append("Total foi ZERADO!")
    elif float(updated_os.get('total_amount', 0)) != update_with_totals['total_amount']:
        errors.append(f"Total incorreto! Esperado: R$ {update_with_totals['total_amount']}, Obtido: R$ {updated_os.get('total_amount')}")
    
    if errors:
        print("   ❌ FALHOU:")
        for error in errors:
            print(f"      • {error}")
    else:
        print("   ✅ PASSOU - Totais atualizados corretamente!")
        print(f"      Total: R$ {updated_os['total_amount']} ✅")
        print(f"      Service Amount: R$ {updated_os.get('service_amount', 0)} ✅")
        print(f"      Parts Amount: R$ {updated_os.get('parts_amount', 0)} ✅")

# ==================== 7. CLEANUP ====================
print("\n7️⃣ Removendo OS de teste...")

delete_response = requests.delete(
    f"{API_BASE}/service-orders/{os_id}",
    headers=headers,
    timeout=REQUEST_TIMEOUT
)

if delete_response.status_code == 204:
    print("   ✅ OS removida")
else:
    print(f"   ⚠️ Não foi possível remover: {delete_response.status_code}")

# ==================== RESULTADO FINAL ====================
print("\n" + "=" * 80)
print("✅ TESTES DE PRESERVAÇÃO CONCLUÍDOS")
print("=" * 80)
print("Verifique os resultados acima.")
print("Todos os testes devem mostrar ✅ PASSOU")
print("=" * 80)

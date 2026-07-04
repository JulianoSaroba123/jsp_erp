"""Verificar dados do sistema"""
import requests

BASE_URL = "http://localhost:8000"

def to_list(data):
    """Converte resposta da API para lista"""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Tenta pegar a lista de dentro do dict (paginação)
        for key in ['customers', 'users', 'products', 'proposals', 'service_orders', 'items']:
            if key in data and isinstance(data[key], list):
                return data[key]
        return []
    return []

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "admin@jsp.com", "password": "123456"}
)

if response.status_code != 200:
    print(f"❌ Erro no login: {response.status_code}")
    exit(1)

token = response.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

print("="*60)
print("  DADOS DO SISTEMA")
print("="*60)

# Clientes
customers_resp = requests.get(f"{BASE_URL}/customers", headers=headers)
customers = to_list(customers_resp.json()) if customers_resp.status_code == 200 else []
print(f"\n📊 CLIENTES: {len(customers)}")
for c in customers[:3]:
    print(f"   • {c.get('name', 'N/A')} (ID: {str(c.get('id', 'N/A'))[:8]}...)")

# Usuários
users_resp = requests.get(f"{BASE_URL}/users", headers=headers)
users = to_list(users_resp.json()) if users_resp.status_code == 200 else []
print(f"\n👥 USUÁRIOS: {len(users)}")
for u in users[:3]:
    roles = u.get('roles', [])
    print(f"   • {u.get('nome', 'N/A')} - Roles: {', '.join(roles) if isinstance(roles, list) else roles}")

# Produtos
products_resp = requests.get(f"{BASE_URL}/products", headers=headers)
products = to_list(products_resp.json()) if products_resp.status_code == 200 else []
print(f"\n📦 PRODUTOS: {len(products)}")

# Proposals existentes
proposals_resp = requests.get(f"{BASE_URL}/proposals", headers=headers)
proposals = to_list(proposals_resp.json()) if proposals_resp.status_code == 200 else []
print(f"\n📄 PROPOSALS: {len(proposals)}")

# Service Orders existentes
os_resp = requests.get(f"{BASE_URL}/service-orders", headers=headers)
service_orders = to_list(os_resp.json()) if os_resp.status_code == 200 else []
print(f"\n🔧 ORDENS DE SERVIÇO: {len(service_orders)}")

print("\n" + "="*60)

if len(customers) == 0:
    print("\n⚠️ AVISO: Nenhum cliente cadastrado!")
    print("   Solução: Vou criar um cliente de teste para você...")
    
    # Criar cliente de teste
    new_customer = {
        "name": "Cliente Teste - Empresa ABC Ltda",
        "contact": "João Silva",
        "phone": "(11) 98765-4321",
        "email": "joao@empresaabc.com.br",
        "address": "Rua Teste, 123 - São Paulo/SP",
        "notes": "Cliente criado automaticamente para testes"
    }
    
    create_resp = requests.post(
        f"{BASE_URL}/customers",
        headers=headers,
        json=new_customer
    )
    
    if create_resp.status_code in [200, 201]:
        customer = create_resp.json()
        print(f"   ✅ Cliente criado: {customer.get('name', 'N/A')}")
        print(f"      ID: {customer.get('id', 'N/A')}")
    else:
        print(f"   ❌ Erro ao criar cliente: {create_resp.status_code}")
        print(f"      {create_resp.text}")


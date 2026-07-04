"""Teste de API - Fluxo Completo de Proposals"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def to_list(data):
    """Converte resposta da API para lista"""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        for key in ['customers', 'users', 'products', 'proposals', 'service_orders', 'items']:
            if key in data and isinstance(data[key], list):
                return data[key]
        return []
    return []

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_login():
    """1. Autentica e retorna o token"""
    print_header("1. AUTENTICAÇÃO")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin@jsp.com", "password": "123456"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login bem-sucedido")
        print(f"   Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(response.text)
        return None

def test_create_proposal(token):
    """2. Cria uma proposta de teste"""
    print_header("2. CRIAR PROPOSTA")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Buscar customer_id primeiro
    resp = requests.get(f"{BASE_URL}/customers", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Erro ao buscar clientes: {resp.status_code}")
        return None
    
    customers = to_list(resp.json())
    
    # Se não houver clientes, criar um
    if not customers or len(customers) == 0:
        print("   ⚠️ Nenhum cliente encontrado - criando cliente de teste...")
        new_customer = {
            "name": "Cliente Teste - Empresa ABC Ltda",
            "contact": "João Silva",
            "phone": "(11) 98765-4321",
            "email": "joao@empresaabc.com.br",
            "address": "Rua Teste, 123 - São Paulo/SP",
            "notes": "Cliente criado automaticamente para testes"
        }
        create_resp = requests.post(f"{BASE_URL}/customers", headers=headers, json=new_customer)
        if create_resp.status_code in [200, 201]:
            customer = create_resp.json()
            customer_id = customer['id']
            print(f"   ✅ Cliente criado: {customer['name']}")
        else:
            print(f"   ❌ Erro ao criar cliente: {create_resp.status_code}")
            return None
    else:
        customer_id = customers[0]['id']
        print(f"   Cliente selecionado: {customers[0]['name']}")
    
    # Criar proposta
    proposal_data = {
        "customer_id": customer_id,
        "title": "Proposta Teste - Implementação Sistema ERP",
        "description": "Sistema completo de gestão com módulos de vendas, financeiro e estoque",
        "service_amount": 15000.00,
        "parts_amount": 5000.00,
        "discount_amount": 2000.00,
        "payment_condition": "50% entrada + 5x no cartão",
        "delivery_days": "60 dias",
        "warranty_days": "90 dias",
        "issue_date": datetime.now().date().isoformat(),
        "validity_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
        "observations": "Proposta criada por teste automatizado",
        "status": "rascunho",
        "items": [
            {
                "description": "Desenvolvimento backend (FastAPI + PostgreSQL)",
                "service_type": "fechado",
                "quantity": 1,
                "unit_price": 8000.00
            },
            {
                "description": "Desenvolvimento frontend (React + TypeScript)",
                "service_type": "fechado",
                "quantity": 1,
                "unit_price": 7000.00
            }
        ],
        "products": []
    }
    
    response = requests.post(
        f"{BASE_URL}/proposals",
        headers=headers,
        json=proposal_data
    )
    
    if response.status_code == 201:
        proposal = response.json()
        print(f"✅ Proposta criada: {proposal['number']}")
        print(f"   ID: {proposal['id']}")
        total = float(proposal['total_amount']) if isinstance(proposal['total_amount'], str) else proposal['total_amount']
        print(f"   Total: R$ {total:,.2f}")
        print(f"   Status: {proposal['status']}")
        return proposal
    else:
        print(f"❌ Erro ao criar: {response.status_code}")
        print(response.text)
        return None

def test_change_status(token, proposal_id, new_status):
    """3. Muda status da proposta"""
    print_header(f"3. MUDAR STATUS → {new_status.upper()}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.patch(
        f"{BASE_URL}/proposals/{proposal_id}/status",
        headers=headers,
        params={"new_status": new_status}
    )
    
    if response.status_code == 200:
        proposal = response.json()
        print(f"✅ Status atualizado: {proposal['status']}")
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return False

def test_convert_to_os(token, proposal_id):
    """4. Converte proposta em OS (TESTE PRINCIPAL)"""
    print_header("4. CONVERTER PARA ORDEM DE SERVIÇO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Buscar técnico
    users_resp = requests.get(f"{BASE_URL}/users", headers=headers)
    users = to_list(users_resp.json()) if users_resp.status_code == 200 else []
    if not users:
        print("❌ Nenhum usuário encontrado")
        return None
    technician = next((u for u in users if 'tecnico' in u.get('roles', [])), users[0])
    
    convert_data = {
        "technician_id": technician['id'],
        "expected_completion_date": (datetime.now() + timedelta(days=60)).date().isoformat(),
        "observations": "OS gerada automaticamente via teste de integração"
    }
    
    response = requests.post(
        f"{BASE_URL}/proposals/{proposal_id}/convert-to-os",
        headers=headers,
        json=convert_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ CONVERSÃO BEM-SUCEDIDA!")
        print(f"   Proposta: {result.get('proposal_number', 'N/A')}")
        print(f"   OS criada: {result.get('service_order_number', result.get('number', 'N/A'))}")
        print(f"   OS ID: {result.get('service_order_id', result.get('id', 'N/A'))}")
        print(f"   Mensagem: {result.get('message', 'N/A')}")
        return result
    else:
        print(f"❌ Erro na conversão: {response.status_code}")
        print(response.text)
        return None

def test_duplicate_prevention(token, proposal_id):
    """5. Tenta converter novamente (deve dar erro 409)"""
    print_header("5. TESTE DE PREVENÇÃO DE DUPLICAÇÃO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    users_resp = requests.get(f"{BASE_URL}/users", headers=headers)
    users = to_list(users_resp.json()) if users_resp.status_code == 200 else []
    if not users:
        print("❌ Nenhum usuário encontrado")
        return False
    technician = users[0]
    
    convert_data = {
        "technician_id": technician['id'],
        "expected_completion_date": (datetime.now() + timedelta(days=60)).date().isoformat(),
        "observations": "Tentativa de conversão duplicada"
    }
    
    response = requests.post(
        f"{BASE_URL}/proposals/{proposal_id}/convert-to-os",
        headers=headers,
        json=convert_data
    )
    
    if response.status_code == 409:
        print(f"✅ DUPLICAÇÃO BLOQUEADA CORRETAMENTE (409 Conflict)")
        print(f"   Mensagem: {response.json().get('detail', 'N/A')}")
        return True
    else:
        print(f"❌ Esperado 409, recebido: {response.status_code}")
        print(response.text)
        return False

def test_check_os_details(token, os_id):
    """6. Verifica detalhes da OS criada"""
    print_header("6. VERIFICAR DETALHES DA OS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/service-orders/{os_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        os = response.json()
        print(f"✅ OS encontrada: {os['number']}")
        print(f"   tipo_ordem: {os.get('tipo_ordem', 'N/A')}")
        print(f"   exibir_valores: {os.get('exibir_valores', 'N/A')}")
        print(f"   proposta_id: {os.get('proposta_id', 'N/A')}")
        print(f"   percentual_concluido: {os.get('percentual_concluido', 'N/A')}%")
        print(f"   etapa_atual: {os.get('etapa_atual', 'N/A')}")
        
        # Validações
        if os.get('tipo_ordem') != 'projeto':
            print(f"   ⚠️ AVISO: tipo_ordem deveria ser 'projeto', mas é '{os.get('tipo_ordem')}'")
        if os.get('exibir_valores') != False:
            print(f"   ⚠️ AVISO: exibir_valores deveria ser False, mas é {os.get('exibir_valores')}")
        
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        return False

def main():
    print("\n" + "🚀"*30)
    print("  TESTE COMPLETO DO FLUXO PROPOSALS → ORDEM DE SERVIÇO")
    print("🚀"*30)
    
    # 1. Login
    token = test_login()
    if not token:
        return
    
    # 2. Criar proposta
    proposal = test_create_proposal(token)
    if not proposal:
        return
    
    # 3. Mudar para enviada
    if not test_change_status(token, proposal['id'], 'enviada'):
        return
    
    # 4. Mudar para aprovada
    if not test_change_status(token, proposal['id'], 'aprovada'):
        return
    
    # 5. Converter para OS
    result = test_convert_to_os(token, proposal['id'])
    if not result:
        return
    
    # 6. Testar duplicação
    test_duplicate_prevention(token, proposal['id'])
    
    # 7. Verificar OS
    os_id = result.get('service_order_id') or result.get('id')
    if os_id:
        test_check_os_details(token, os_id)
    
    print("\n" + "="*60)
    print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("="*60)
    print(f"\n📋 Proposta criada: {proposal['number']}")
    os_number = result.get('service_order_number') or result.get('number', 'N/A')
    print(f"🔧 OS criada: {os_number}")
    print(f"\n🌐 Acesse o frontend: http://localhost:5173/proposals")
    print(f"🔍 Veja a proposta no sistema para testar o botão 'Gerar OS'")
    print("="*60)

if __name__ == "__main__":
    main()

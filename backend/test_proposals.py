import requests
import json

print("=" * 60)
print("TESTE - Endpoint de Propostas")
print("=" * 60)

# 1. Fazer login para obter token
print("\n[1] Fazendo login...")
try:
    response = requests.post(
        "http://localhost:8000/auth/login",
        data={"username": "admin@jsp.com", "password": "123456"},
        timeout=5
    )
    if response.status_code == 200:
        data = response.json()
        token = data['access_token']
        print(f"✅ Login OK - Token obtido")
    else:
        print(f"❌ Erro no login: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Exceção no login: {e}")
    exit(1)

# 2. Testar GET /proposals
print("\n[2] Testando GET /proposals...")
try:
    response = requests.get(
        "http://localhost:8000/proposals?page=1&page_size=15",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCESSO!")
        print(f"   Total de propostas: {data.get('total', 0)}")
        print(f"   Página: {data.get('page', 1)}")
        print(f"   Items retornados: {len(data.get('items', []))}")
        
        if data.get('items'):
            print("\n   Propostas encontradas:")
            for i, prop in enumerate(data['items'][:3], 1):
                print(f"     {i}. {prop.get('number')} - {prop.get('status')}")
    else:
        print(f"❌ Erro: {response.text[:300]}")
except Exception as e:
    print(f"❌ Exceção: {e}")

print("\n" + "=" * 60)

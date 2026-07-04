"""
Teste de login via API para verificar autenticação.

Testa:
1. POST /auth/login com credenciais corretas
2. GET /auth/me com token obtido
"""
import requests

API_BASE = "http://localhost:8000"

print("=" * 70)
print("TESTE DE LOGIN - ERP JSP")
print("=" * 70)

# Teste 1: Login com credenciais corretas
print("\n1️⃣ Testando login com admin@jsp.com / admin123...")

try:
    # OAuth2PasswordRequestForm exige application/x-www-form-urlencoded
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={
            "username": "admin@jsp.com",  # OAuth2 usa "username" mas aceita email
            "password": "admin123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=5
    )
    
    if response.status_code == 200:
        print("   ✅ Login realizado com sucesso!")
        
        data = response.json()
        access_token = data.get("access_token")
        user = data.get("user")
        
        print(f"   🔑 Token obtido: {access_token[:50]}...")
        print(f"   👤 Usuário: {user.get('name')} ({user.get('email')})")
        print(f"   📋 Role: {user.get('role')}")
        
        # Teste 2: Usar token para acessar /auth/me
        print("\n2️⃣ Testando acesso autenticado (/auth/me)...")
        
        me_response = requests.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        
        if me_response.status_code == 200:
            print("   ✅ Autenticação com token funcionando!")
            me_data = me_response.json()
            print(f"   👤 Dados retornados: {me_data.get('name')} ({me_data.get('email')})")
        else:
            print(f"   ❌ Erro ao acessar /auth/me: {me_response.status_code}")
            print(f"   Resposta: {me_response.text}")
    
    elif response.status_code == 401:
        print("   ❌ Credenciais inválidas (401 Unauthorized)")
        print(f"   Resposta: {response.json()}")
    
    else:
        print(f"   ❌ Erro inesperado: {response.status_code}")
        print(f"   Resposta: {response.text}")

except requests.exceptions.ConnectionError:
    print("   ❌ ERRO: Backend não está rodando na porta 8000!")
    print("   Execute: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

except Exception as e:
    print(f"   ❌ Erro durante o teste: {e}")

print("\n" + "=" * 70)
print("TESTE CONCLUÍDO")
print("=" * 70)

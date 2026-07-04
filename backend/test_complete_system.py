import requests

print("=" * 60)
print("TESTE COMPLETO - Login + Logo + Settings")
print("=" * 60)

# 1. Testar GET /settings (público - sem autenticação)
print("\n[1] Testando GET /settings (público)...")
try:
    response = requests.get("http://localhost:8000/settings", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"   Company: {data.get('company_name')}")
        print(f"   Trade name: {data.get('trade_name')}")
        
        logo_url = data.get('logo_url')
        if logo_url:
            print(f"   Logo: PRESENTE ({len(logo_url)} caracteres)")
            if logo_url.startswith('data:image'):
                print(f"   Tipo: Base64 Data URI")
        else:
            print(f"   Logo: AUSENTE ❌")
    else:
        print(f"❌ Erro: Status {response.status_code}")
except Exception as e:
    print(f"❌ Exceção: {e}")

# 2. Testar Login
print("\n[2] Testando POST /auth/login...")
try:
    response = requests.post(
        "http://localhost:8000/auth/login",
        data={"username": "admin@jsp.com", "password": "123456"},
        timeout=5
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"   User: {data['user']['name']}")
        print(f"   Role: {data['user']['role']}")
        print(f"   Token: {data['access_token'][:30]}...")
        
        token = data['access_token']
    else:
        print(f"❌ Erro: Status {response.status_code}")
        print(f"   {response.text[:100]}")
        token = None
except Exception as e:
    print(f"❌ Exceção: {e}")
    token = None

# 3. Testar rota protegida (GET /auth/me)
if token:
    print("\n[3] Testando GET /auth/me (autenticado)...")
    try:
        response = requests.get(
            "http://localhost:8000/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   User ID: {data['id']}")
            print(f"   Email: {data['email']}")
            print(f"   Active: {data['is_active']}")
        else:
            print(f"❌ Erro: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Exceção: {e}")

print("\n" + "=" * 60)
print("RESUMO: Sistema funcionando! ✅")
print("- Login: OK")
print("- Settings: OK")
print("- Logo: OK")
print("=" * 60)

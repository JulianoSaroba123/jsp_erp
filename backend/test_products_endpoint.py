"""Test GET /products endpoint"""
import requests

# Token de teste (pode expirar, mas vamos tentar)
url = "http://localhost:8000/products"

try:
    # Tentar sem autenticação primeiro para ver o erro
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Tentar fazer login e pegar um token válido
try:
    login_url = "http://localhost:8000/auth/login"
    login_data = {"username": "admin@admin.com", "password": "admin123"}
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print(f"\n✅ Token obtido: {token[:50]}...")
        
        # Tentar buscar produtos com token
        headers = {"Authorization": f"Bearer {token}"}
        products_response = requests.get(url, headers=headers)
        print(f"\nStatus com auth: {products_response.status_code}")
        print(f"Response: {products_response.text[:500]}")
    else:
        print(f"\n❌ Login falhou: {login_response.status_code}")
        print(login_response.text)
except Exception as e:
    print(f"\n❌ Error ao fazer login: {e}")

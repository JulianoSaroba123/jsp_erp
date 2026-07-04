"""
Teste dos endpoints de módulos (proposals, customers, products, service_orders)
"""
import requests

BASE_URL = "http://localhost:8000"

def test_all_modules():
    print("=" * 60)
    print("TESTE - Todos os Módulos")
    print("=" * 60)
    
    # Login
    print("\n[1] Fazendo login...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin@jsp.com", "password": "123456"}  # Form-data, não JSON!
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login falhou: {login_response.status_code}")
        try:
            print(f"   Erro: {login_response.json()}")
        except:
            print(f"   Response: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login OK")
    
    # Testar cada módulo
    modules = [
        ("Proposals", "/proposals"),
        ("Customers", "/customers"),
        ("Products", "/products"),
        ("Service Orders", "/service-orders"),
        ("Suppliers", "/suppliers"),
        ("Orders", "/orders")
    ]
    
    print("\n[2] Testando endpoints de listagem...")
    results = []
    
    for module_name, endpoint in modules:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            status = response.status_code
            
            if status == 200:
                data = response.json()
                # Tentar extrair informações de paginação
                if isinstance(data, dict):
                    items = data.get('items', [])
                    total = data.get('total', len(items))
                    print(f"   ✅ {module_name:20} | Status: {status} | Total: {total} items")
                    results.append((module_name, "OK", total))
                else:
                    count = len(data) if isinstance(data, list) else 'N/A'
                    print(f"   ✅ {module_name:20} | Status: {status} | Dados: {count}")
                    results.append((module_name, "OK", count))
            else:
                print(f"   ❌ {module_name:20} | Status: {status}")
                try:
                    error = response.json().get('detail', 'Unknown error')
                    print(f"      Erro: {error}")
                except:
                    pass
                results.append((module_name, "FALHOU", status))
        except Exception as e:
            print(f"   ❌ {module_name:20} | Erro: {str(e)}")
            results.append((module_name, "ERRO", str(e)))
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO:")
    success = sum(1 for _, status, _ in results if status == "OK")
    total = len(results)
    print(f"   {success}/{total} módulos funcionando")
    
    if success == total:
        print("   ✅ TODOS OS MÓDULOS OK!")
    else:
        print("   ⚠️ Alguns módulos com problema")
        for name, status, info in results:
            if status != "OK":
                print(f"      - {name}: {status} ({info})")
    
    print("=" * 60)

if __name__ == "__main__":
    test_all_modules()

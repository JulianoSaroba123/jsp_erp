import requests
import time

# Aguardar reload do backend
time.sleep(2)

print("Testando GET /settings...")
try:
    response = requests.get("http://localhost:8000/settings", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ SUCESSO!")
        data = response.json()
        print(f"Encontrou {len(data)} campos")
        # Verificar campos PDF
        for field in ['pdf_header_text', 'pdf_footer_text', 'default_proposal_message']:
            if field in data:
                print(f"  ✓ {field}: {str(data[field])[:50]}...")
            else:
                print(f"  ✗ {field}: NÃO ENCONTRADO")
    else:
        print(f"❌ Erro: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exceção: {e}")

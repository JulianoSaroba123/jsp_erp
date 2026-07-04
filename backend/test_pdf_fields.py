"""
Script de teste para verificar campos PDF no Settings
"""
import requests
import json

print("=" * 60)
print("TESTE: Verificação de Campos PDF no Settings")
print("=" * 60)

# 1. Testar GET /settings
print("\n[1] Testando GET /settings...")
try:
    response = requests.get("http://localhost:8000/settings")
    response.raise_for_status()
    data = response.json()
    print("✓ GET /settings OK (Status 200)")
    
    # Verificar campos PDF
    print("\n[2] Verificando campos PDF...")
    campos_pdf = {
        'pdf_header_text': data.get('pdf_header_text'),
        'pdf_footer_text': data.get('pdf_footer_text'),
        'default_proposal_message': data.get('default_proposal_message')
    }
    
    for campo, valor in campos_pdf.items():
        if valor is not None:
            preview = str(valor)[:50] + "..." if len(str(valor)) > 50 else str(valor)
            print(f"✓ {campo}: PRESENTE")
            print(f"  Valor: {preview}")
        else:
            print(f"✗ {campo}: AUSENTE")
    
    # Verificar outros campos essenciais
    print("\n[3] Verificando campos essenciais...")
    essenciais = ['company_name', 'logo_url', 'mission', 'vision', 'values']
    for campo in essenciais:
        valor = data.get(campo)
        status = "✓" if valor else "✗"
        print(f"{status} {campo}: {'PRESENTE' if valor else 'AUSENTE'}")
    
    print("\n" + "=" * 60)
    print("RESULTADO: Todos os campos verificados!")
    print("=" * 60)
    
except requests.exceptions.ConnectionError:
    print("✗ ERRO: Backend não está rodando na porta 8000")
except requests.exceptions.HTTPError as e:
    print(f"✗ ERRO HTTP: {e}")
except Exception as e:
    print(f"✗ ERRO: {e}")

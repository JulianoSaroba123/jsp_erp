import requests
import json

# 1. Fazer login usando form-data (OAuth2PasswordRequestForm)
print("1. Fazendo login...")
login_url = "http://localhost:8000/auth/login"
login_data = {
    "username": "admin@jsp.com",  # OAuth2 usa "username" mas aqui é email
    "password": "123456"
}

response = requests.post(login_url, data=login_data)  # Usar data= para form-data
print(f"Status login: {response.status_code}")

if response.status_code == 200:
    token_data = response.json()
    token = token_data.get('access_token')
    print(f"[OK] Token obtido: {token[:50]}...")
    
    # 2. Testar endpoint de PDF
    print("\n2. Testando PDF...")
    proposal_id = "710a89c9-84f9-4ad5-a47a-96ae85460c1d"
    pdf_url = f"http://localhost:8000/proposals/{proposal_id}/pdf"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    pdf_response = requests.get(pdf_url, headers=headers)
    print(f"Status PDF: {pdf_response.status_code}")
    
    if pdf_response.status_code == 200:
        # Salvar PDF
        with open("proposta_teste.pdf", "wb") as f:
            f.write(pdf_response.content)
        print(f"[OK] PDF salvo com sucesso! ({len(pdf_response.content)} bytes)")
        print("Arquivo: proposta_teste.pdf")
    else:
        print(f"[ERRO] Erro ao gerar PDF:")
        print(f"Status: {pdf_response.status_code}")
        print(f"Resposta: {pdf_response.text[:500]}")
        
    # 3. Mostrar token para usar no frontend
    print(f"\n3. Token para usar no localStorage:")
    print(f"Token: {token}")
    
else:
    print(f"[ERRO] Erro no login:")
    print(response.text)

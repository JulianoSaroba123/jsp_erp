"""
==============================================
VALIDAÇÃO FINAL: Sistema de Textos Padrão PDF
==============================================
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("VALIDAÇÃO COMPLETA - Textos Padrão do PDF")
print("="*60)

# ======== TESTE 1: GET /settings ========
print("\n[TESTE 1] GET /settings")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/settings")
    if response.status_code == 200:
        print("✓ Endpoint responde: Status 200 OK")
        data = response.json()
        
        # Verificar campos PDF
        campos =  {
            'pdf_header_text': data.get('pdf_header_text'),
            'pdf_footer_text': data.get('pdf_footer_text'),
            'default_proposal_message': data.get('default_proposal_message')
        }
        
        todos_presentes = True
        for campo, valor in campos.items():
            if valor is not None:
                preview = str(valor).replace('\n', ' ')[:60] + "..."
                print(f"✓ {campo}: PRESENTE")
                print(f"  → {preview}")
            else:
                print(f"✗ {campo}: AUSENTE (NULL)")
                todos_presentes = False
        
        if todos_presentes:
            print("\n✅ TESTE 1: APROVADO - Todos os campos presentes")
        else:
            print("\n⚠️  TESTE 1: PARCIAL - Alguns campos ausentes")
    else:
        print(f"✗ Erro HTTP {response.status_code}")
        print(f"  Resposta: {response.text[:200]}")
        print("\n❌ TESTE 1: FALHOU")
except Exception as e:
    print(f"✗ Erro de conexão: {e}")
    print("\n❌ TESTE 1: FALHOU - Backend não acessível")

# ======== TESTE 2: Estrutura do Template ========  
print("\n[TESTE 2] Verificar Template PDF")
print("-" * 60)
try:
    with open('app/templates/proposal_pdf.html', 'r', encoding='utf-8') as f:
        template = f.read()
    
    checks = {
        'company.pdf_header_text': 'company.pdf_header_text' in template,
        'company.pdf_footer_text': 'company.pdf_footer_text' in template,
        'company.default_proposal_message': 'company.default_proposal_message' in template
    }
    
    for check_name, found in checks.items():
        if found:
            print(f"✓ Template usa: {check_name}")
        else:
            print(f"✗ Template NÃO usa: {check_name}")
    
    if all(checks.values()):
        print("\n✅ TESTE 2: APROVADO - Template configurado")
    else:
        print("\n❌ TESTE 2: FALHOU - Template incompleto")
        
except Exception as e:
    print(f"✗ Erro ao ler template: {e}")
    print("\n❌ TESTE 2: FALHOU")

# ======== TESTE 3: Banco de Dados ========
print("\n[TESTE 3] Verificar Banco de Dados")
print("-" * 60)
try:
    from sqlalchemy import create_engine, text
    engine = create_engine("postgresql+psycopg://jsp_user:jsp123456@localhost:5433/jsp_erp")
    
    with engine.connect() as conn:
        # Verificar colunas
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'settings' 
            AND column_name IN ('pdf_header_text', 'pdf_footer_text', 'default_proposal_message')
        """))
        
        colunas = [row[0] for row in result]
        
        if len(colunas) == 3:
            print(f"✓ Colunas existem no banco: {', '.join(colunas)}")
        else:
            print(f"✗ Colunas faltando. Encontradas: {colunas}")
        
        # Verificar dados
        result = conn.execute(text("""
            SELECT 
                pdf_header_text IS NOT NULL as has_header, 
                pdf_footer_text IS NOT NULL as has_footer,
                default_proposal_message IS NOT NULL as has_message
            FROM public.settings LIMIT 1
        """))
        
        row = result.fetchone()
        if row:
            has_data = all([row[0], row[1], row[2]])
            if has_data:
                print("✓ Dados populados no banco")
                print("\n✅ TESTE 3: APROVADO - Banco configurado")
            else:
                print("⚠️  Algumas colunas estão NULL")
                print("\n⚠️  TESTE 3: PARCIAL - Dados incompletos")
        else:
            print("✗ Nenhuma configuração encontrada")
            print("\n❌ TESTE 3: FALHOU")
            
except Exception as e:
    print(f"✗ Erro de banco: {e}")
    print("\n❌ TESTE 3: FALHOU")

# ======== RESUMO FINAL ========
print("\n" + "="*60)
print("RESUMO DA VALIDAÇÃO")
print("="*60)
print("\n📋 Checklist:")
print("  [ ] Backend rodando (porta 8000)")
print("  [ ] Endpoint GET /settings retorna campos PDF")
print("  [ ] Template PDF configurado com campos")
print("  [ ] Banco de dados com colunas e dados")
print("\n💡 Próximos passos:")
print("  1. Testar atualização via PUT /settings")
print("  2. Gerar PDF de teste e verificar visualmente")
print("  3. Testar upload de logo")
print("\n" + "="*60)

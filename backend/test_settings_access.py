"""
Teste direto de conexão e query na tabela settings
"""
from app.database import SessionLocal
from app.models.settings import Settings

print("🔍 Testando acesso à tabela settings...")

db = SessionLocal()

try:
    # Tentar consultar settings
    count = db.query(Settings).count()
    print(f"✅ Tabela acessível! Total de registros: {count}")
    
    # Tentar buscar settings
    settings = db.query(Settings).first()
    if settings:
        print(f"✅ Dados encontrados:")
        print(f"   - Empresa: {settings.company_name}")
        print(f"   - Cidade: {settings.city}/{settings.state}")
        print(f"   - Logo: {settings.logo_url or '(não configurado)'}")
    else:
        print("⚠️ Nenhum registro encontrado")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

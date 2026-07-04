"""Teste direto usando o modelo Settings"""
from app.database import SessionLocal
from app.models.settings import Settings

db = SessionLocal()
try:
    print("Tentando query no Settings...")
    settings = db.query(Settings).first()
    if settings:
        print(f"✅ Sucesso! company_name: {settings.company_name}, city: {settings.city}")
    else:
        print("❌ Nenhum registro encontrado")
except Exception as e:
    print(f"❌ Erro: {e}")
finally:
    db.close()

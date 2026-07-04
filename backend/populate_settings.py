"""
Script para popular a tabela Settings com dados iniciais do .env
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.settings import Settings
from uuid import UUID

SETTINGS_ID = UUID("00000000-0000-0000-0000-000000000001")

def populate_settings():
    """Cria ou atualiza o registro de settings com dados do .env"""
    db = SessionLocal()
    
    try:
        # Verificar se já existe
        settings = db.query(Settings).filter(Settings.id == SETTINGS_ID).first()
        
        if settings:
            print(f"✅ Settings já existem: {settings.company_name}")
            print(f"   Logo URL: {settings.logo_url or '(não configurado)'}")
        else:
            # Criar novo registro
            settings = Settings(
                id=SETTINGS_ID,
                company_name=os.getenv("COMPANY_NAME", ""),
                trade_name=os.getenv("COMPANY_TRADE_NAME"),
                cnpj=os.getenv("COMPANY_CNPJ"),
                email=os.getenv("COMPANY_EMAIL"),
                phone=os.getenv("COMPANY_PHONE"),
                phone_2=os.getenv("COMPANY_PHONE_2"),
                website=os.getenv("COMPANY_WEBSITE"),
                cep=os.getenv("COMPANY_CEP"),
                street=os.getenv("COMPANY_STREET"),
                number=os.getenv("COMPANY_NUMBER"),
                neighborhood=os.getenv("COMPANY_NEIGHBORHOOD"),
                city=os.getenv("COMPANY_CITY"),
                state=os.getenv("COMPANY_STATE"),
                logo_url=os.getenv("COMPANY_LOGO_URL"),
                bank_name=os.getenv("COMPANY_BANK_NAME"),
                bank_agency=os.getenv("COMPANY_BANK_AGENCY"),
                bank_account=os.getenv("COMPANY_BANK_ACCOUNT"),
                pix_key=os.getenv("COMPANY_PIX_KEY"),
                mission=os.getenv("COMPANY_MISSION"),
                vision=os.getenv("COMPANY_VISION"),
                values=os.getenv("COMPANY_VALUES"),
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
            
            print(f"✅ Settings criado com sucesso!")
            print(f"   Empresa: {settings.company_name}")
            print(f"   CNPJ: {settings.cnpj}")
            print(f"   Cidade: {settings.city}/{settings.state}")
            print(f"   Logo: {settings.logo_url or '(não configurado)'}")
        
        return settings
        
    except Exception as e:
        print(f"❌ Erro ao popular settings: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Populando tabela Settings com dados do .env...\n")
    populate_settings()
    print("\n✅ Concluído!")

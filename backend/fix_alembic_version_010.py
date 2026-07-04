"""
Script para corrigir versão do Alembic
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Verificar versão atual
    result = conn.execute(text("SELECT version_num FROM core.alembic_version"))
    current = result.fetchone()
    print(f"Versão atual no alembic_version: {current[0] if current else 'NENHUMA'}")
    
    # Atualizar para 010_create_suppliers (última antes da nova migration)
    conn.execute(text("UPDATE core.alembic_version SET version_num = '010_create_suppliers'"))
    conn.commit()
    
    print("✅ Versão atualizada para: 010_create_suppliers")
    print("   Agora você pode rodar: alembic upgrade head")

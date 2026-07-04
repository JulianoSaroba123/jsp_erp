"""Teste direto de query no banco"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Testa com e sem search_path
print("=== Teste 1: Engine sem search_path ===")
engine1 = create_engine(DATABASE_URL, pool_pre_ping=True)
try:
    with engine1.connect() as conn:
        result = conn.execute(text("SELECT company_name, city FROM settings LIMIT 1"))
        row = result.fetchone()
        print(f"✅ Sucesso: {row}")
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n=== Teste 2: Engine COM search_path=public,core ===")
engine2 = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"options": "-c search_path=public,core"}
)
try:
    with engine2.connect() as conn:
        result = conn.execute(text("SELECT company_name, city FROM settings LIMIT 1"))
        row = result.fetchone()
        print(f"✅ Sucesso: {row}")
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n=== Teste 3: Query com schema explícito ===")
try:
    with engine2.connect() as conn:
        result = conn.execute(text("SELECT company_name, city FROM public.settings LIMIT 1"))
        row = result.fetchone()
        print(f"✅ Sucesso: {row}")
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n=== Teste 4: Verificar search_path ===")
try:
    with engine2.connect() as conn:
        result = conn.execute(text("SHOW search_path"))
        row = result.fetchone()
        print(f"✅ Search path: {row}")
except Exception as e:
    print(f"❌ Erro: {e}")

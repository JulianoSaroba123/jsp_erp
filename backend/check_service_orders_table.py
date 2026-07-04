"""Verifica estrutura da tabela service_orders"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Verifica se a tabela existe
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'core' 
          AND table_name = 'service_orders'
        ORDER BY ordinal_position
    """))
    
    rows = list(result)
    
    if not rows:
        print("❌ Tabela service_orders NÃO EXISTE no schema core")
    else:
        print(f"✅ Tabela service_orders encontrada com {len(rows)} colunas:\n")
        for row in rows:
            print(f"  - {row[0]:<30} | {row[1]:<20} | Nullable: {row[2]}")

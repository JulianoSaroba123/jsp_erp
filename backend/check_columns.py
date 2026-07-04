"""Check current columns in products table"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    columns = conn.execute(text("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns 
        WHERE table_schema='core' AND table_name='products'
        ORDER BY ordinal_position
    """)).fetchall()
    
    print(f"📋 Colunas da tabela core.products ({len(columns)}):\n")
    for col_name, dtype, max_len, nullable in columns:
        len_str = f"({max_len})" if max_len else ""
        null_str = "NULL" if nullable == 'YES' else "NOT NULL"
        print(f"  {col_name:20} {dtype}{len_str:15} {null_str}")

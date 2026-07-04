"""
Script para adicionar manualmente as 7 novas colunas em core.customers
"""
from app.database import engine
from sqlalchemy import text

sql_commands = [
    "ALTER TABLE core.customers ADD COLUMN IF NOT EXISTS person_type VARCHAR(2) DEFAULT 'PF';",
    "ALTER TABLE core.customers ADD COLUMN IF NOT EXISTS trade_name VARCHAR(120);",
    "ALTER TABLE core.customers ADD COLUMN IF NOT EXISTS state_registration VARCHAR(20);",
    "ALTER TABLE core.customers ADD COLUMN IF NOT EXISTS phone2 VARCHAR(15);",
    "ALTER TABLE core.customers ADD COLUMN IF NOT EXISTS address_complement VARCHAR(100);",
    "ALTER TABLE core.customers ADD COLUMN IF NOT EXISTS notes TEXT;",
    "ALTER TABLE core.customers ADD COLUMN IF NOT EXISTS status VARCHAR(10) DEFAULT 'active' NOT NULL;",
]

print("Adicionando 7 novas colunas em core.customers...")

with engine.connect() as conn:
    for sql in sql_commands:
        try:
            conn.execute(text(sql))
            conn.commit()
            print(f"✓ {sql.split('ADD COLUMN IF NOT EXISTS ')[1].split(' ')[0]}")
        except Exception as e:
            print(f"✗ Erro: {e}")
            conn.rollback()

print("\n✅ Concluído!")

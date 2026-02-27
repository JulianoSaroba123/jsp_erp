"""Verificar tabelas no schema core"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'core' "
        "ORDER BY table_name"
    ))
    
    print("Tabelas no schema 'core':")
    print("=" * 40)
    for row in result:
        print(f"  - {row[0]}")
    print("=" * 40)

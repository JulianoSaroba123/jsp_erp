"""Check products table comprehensive"""
from app.database import engine
from sqlalchemy import text, inspect

with engine.connect() as conn:
    # Check if table exists in any schema
    result = conn.execute(text("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name='products'
    """)).fetchall()
    
    if result:
        print(f"✅ Tabela 'products' encontrada em {len(result)} schema(s):")
        for schema, name in result:
            print(f"  - {schema}.{name}")
    else:
        print("❌ Tabela 'products' NÃO encontrada em nenhum schema!")
    
    # Check core schema tables
    core_tables = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='core'
        ORDER BY table_name
    """)).fetchall()
    
    print(f"\n📋 Tabelas no schema 'core' ({len(core_tables)}):")
    for (table,) in core_tables:
        print(f"  - {table}")

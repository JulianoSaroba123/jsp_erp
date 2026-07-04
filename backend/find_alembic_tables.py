"""Find all alembic_version tables"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Find all alembic_version tables
    result = conn.execute(text("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name = 'alembic_version'
    """)).fetchall()
    
    print(f"📋 Tabelas alembic_version encontradas: {len(result)}\n")
    
    for schema, table in result:
        print(f"  Schema: {schema}")
        try:
            rows = conn.execute(text(f'SELECT version_num FROM {schema}.{table}')).fetchall()
            if rows:
                for row in rows:
                    print(f"    ✅ Versão: {row[0]}")
            else:
                print(f"    ⚠️  Vazia")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        print()

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text('SELECT version_num FROM alembic_version')).fetchone()
    if result:
        print(f"Versão atual do Alembic: {result[0]}")
    else:
        print("Nenhuma versão do Alembic encontrada")
        
    # Verificar se tabela service_order_items existe
    tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='core' AND table_name LIKE '%service_order%'")).fetchall()
    print("\nTabelas service_order encontradas:")
    for table in tables:
        print(f"  - {table[0]}")
        
except Exception as e:
    print(f"Erro: {e}")
finally:
    db.close()

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Verificar schema de todas as tabelas relacionadas

tables_to_check = ['service_orders', 'proposals', 'products', 'customers']

for table in tables_to_check:
    result = db.execute(text(
        f"SELECT table_schema FROM information_schema.tables WHERE table_name = '{table}'"
    ))
    schemas = [row[0] for row in result.fetchall()]
    if schemas:
        print(f"{table}: {', '.join(schemas)}")
    else:
        print(f"{table}: NOT FOUND")

db.close()

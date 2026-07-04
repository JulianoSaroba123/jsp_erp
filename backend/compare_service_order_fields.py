"""Compara campos da tabela com o modelo Python"""
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
from app.models.service_order import ServiceOrder

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Campos no banco
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns 
        WHERE table_schema = 'core' 
          AND table_name = 'service_orders'
        ORDER BY ordinal_position
    """))
    
    db_columns = {row[0] for row in result}

# Campos no modelo Python
mapper = inspect(ServiceOrder)
model_columns = {col.key for col in mapper.columns}

# Comparação
missing_in_model = db_columns - model_columns
extra_in_model = model_columns - db_columns

print("🔍 COMPARAÇÃO MODELO vs BANCO\n")

if missing_in_model:
    print(f"❌ Campos no BANCO mas FALTANDO no modelo ({len(missing_in_model)}):")
    for col in sorted(missing_in_model):
        print(f"   - {col}")
else:
    print("✅ Todos os campos do banco estão no modelo")

print()

if extra_in_model:
    print(f"⚠️  Campos no MODELO mas NÃO no banco ({len(extra_in_model)}):")
    for col in sorted(extra_in_model):
        print(f"   - {col}")
else:
    print("✅ Todos os campos do modelo existem no banco")

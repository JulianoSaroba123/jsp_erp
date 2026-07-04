"""
Script para verificar tabelas no schema core
"""
import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

# Criar engine
engine = create_engine(os.getenv('DATABASE_URL'))

# Inspecionar tabelas
inspector = inspect(engine)
tables = inspector.get_table_names(schema='core')

print("=" * 80)
print("TABELAS NO SCHEMA CORE:")
print("=" * 80)
for table in sorted(tables):
    print(f"  - {table}")
print("=" * 80)
print(f"Total: {len(tables)} tabelas")

# Verificar especificamente se products existe
if 'products' in tables:
    print("\n✅ Tabela 'products' EXISTE")
    columns = [col['name'] for col in inspector.get_columns('products', schema='core')]
    print(f"   Total de colunas: {len(columns)}")
else:
    print("\n❌ Tabela 'products' NÃO EXISTE")

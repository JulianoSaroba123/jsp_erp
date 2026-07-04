from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)

if 'customers' in inspector.get_table_names(schema='core'):
    cols = [c['name'] for c in inspector.get_columns('customers', schema='core')]
    print(f'✓ Tabela core.customers existe com {len(cols)} colunas:')
    for col in cols:
        print(f'  - {col}')
else:
    print('✗ Tabela core.customers NÃO existe')

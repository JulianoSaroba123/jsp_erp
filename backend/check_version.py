"""Check alembic version in database"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM core.alembic_version')).fetchone()
    if result:
        print(f'📌 Versão atual no banco: {result[0]}')
    else:
        print('⚠️ Nenhuma versão registrada em alembic_version!')
    
    # Also check if we can access the products table directly
    try:
        count = conn.execute(text('SELECT COUNT(*) FROM core.products')).fetchone()
        print(f'✅ Tabela core.products acessível: {count[0]} registros')
    except Exception as e:
        print(f'❌ Erro ao acessar core.products: {e}')

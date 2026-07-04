"""Script temporário para checar versão do alembic"""
from sqlalchemy import text
from app.security.deps import get_db

db = next(get_db())
result = db.execute(text('SELECT version_num FROM core.alembic_version')).fetchone()
print('🔍 Versão Alembic:', result[0] if result else 'NENHUMA')
db.close()

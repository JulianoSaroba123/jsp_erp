from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM core.proposals'))
    count = result.scalar()
    print(f'✅ Total de propostas: {count}')
    
    if count > 0:
        result = conn.execute(text('SELECT id, number FROM core.proposals LIMIT 1'))
        row = result.fetchone()
        print(f'✅ Primeira proposta: {row[1]} (ID: {row[0]})')

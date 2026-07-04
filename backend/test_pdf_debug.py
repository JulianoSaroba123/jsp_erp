import asyncio
from app.database import engine
from sqlalchemy import text

# Verificar propostas disponíveis
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT id, number, title, customer_id, status 
        FROM core.proposals 
        ORDER BY created_at DESC 
        LIMIT 5
    '''))
    
    print("\n=== PROPOSTAS DISPONÍVEIS ===")
    for row in result:
        print(f"ID: {row[0]} | Número: {row[1]} | Título: {row[2]} | Status: {row[4]}")
    print()

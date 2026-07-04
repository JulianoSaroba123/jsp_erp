from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT id, email, name, is_active FROM core.users LIMIT 5'))
    users = result.fetchall()
    
print("\n=== USUÁRIOS CADASTRADOS ===")
for user in users:
    print(f"Email: {user[1]} | Nome: {user[2]} | Ativo: {user[3]}")
print()

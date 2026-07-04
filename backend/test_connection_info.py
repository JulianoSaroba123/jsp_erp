"""Verificar qual banco e usuário"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DATABASE_URL: {DATABASE_URL}\n")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

with engine.connect() as conn:
    # Ver banco atual
    result = conn.execute(text("SELECT current_database()"))
    print(f"Banco atual: {result.fetchone()[0]}")
    
    # Ver usuário atual
    result = conn.execute(text("SELECT current_user"))
    print(f"Usuário atual: {result.fetchone()[0]}")
    
    # Ver schemas disponíveis
    result = conn.execute(text("SELECT schema_name FROM information_schema.schemata"))
    print(f"\nSchemas disponíveis:")
    for row in result:
        print(f"  - {row[0]}")
    
    # Ver tabelas em public
    result = conn.execute(text("""
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname IN ('public', 'core')
        ORDER BY schemaname, tablename
    """))
    print(f"\nTabelas em public e core:")
    for row in result:
        print(f"  - {row[0]}.{row[1]}")

"""
Teste direto com psycopg (sem SQLAlchemy)
"""
import psycopg

DATABASE_URL = "postgresql://jsp_user:jsp123456@localhost:5432/jsp_erp"

print(f"Conectando: {DATABASE_URL}")

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        print("\n=== Schemas ===")
        cur.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
        for row in cur.fetchall():
            print(f"  - {row[0]}")
        
        print("\n=== Tabelas em core ===")
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'core' ORDER BY tablename")
        for row in cur.fetchall():
            print(f"  - {row[0]}")
        
        print("\n=== COUNT em core.orders ===")
        cur.execute("SELECT COUNT(*) FROM core.orders")
        count = cur.fetchone()[0]
        print(f"  Total: {count}")
        
        print("\n=== Primeiras 3 orders ===")
        cur.execute("SELECT id, description, total FROM core.orders LIMIT 3")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} (R$ {row[2]})")

print("\n✓ Teste com psycopg direto funcionou!")

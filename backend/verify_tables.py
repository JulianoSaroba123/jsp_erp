import psycopg
conn = psycopg.connect('postgresql://jsp_user:jsp123456@localhost:5432/jsp_erp')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'core' AND table_name LIKE 'service_order%' ORDER BY table_name")
rows = cur.fetchall()
print("\n" + "="*80)
print("TABELAS DE SERVICE ORDERS CRIADAS:")
print("="*80)
for row in rows:
    print(f"  ✓ core.{row[0]}")
print("="*80)
print(f"Total: {len(rows)} tabelas\n")

# Verificar versão do Alembic
cur.execute("SELECT version_num FROM core.alembic_version")
version = cur.fetchone()
print(f"Versão do Alembic: {version[0] if version else 'NENHUMA'}\n")

cur.close()
conn.close()

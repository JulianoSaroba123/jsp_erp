"""
Script de teste de conexão e verificação da tabela core.orders
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"DATABASE_URL: {DATABASE_URL}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("\n=== Testando conexão ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(f"✓ Conexão OK: {result.scalar()}")

print("\n=== Verificando schemas ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"))
    schemas = [row[0] for row in result]
    print(f"Schemas disponíveis: {schemas}")
    print(f"'core' existe? {'core' in schemas}")

print("\n=== Verificando tabelas no schema core ===")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'core'
        ORDER BY tablename
    """))
    tables = [row[0] for row in result]
    print(f"Tabelas em core: {tables}")
    print(f"'orders' existe? {'orders' in tables}")

print("\n=== Testando SELECT direto em core.orders ===")
with engine.connect() as conn:
    try:
        result = conn.execute(text("SELECT COUNT(*) FROM core.orders"))
        count = result.scalar()
        print(f"✓ SELECT COUNT(*) FROM core.orders = {count}")
    except Exception as e:
        print(f"✗ Erro: {e}")

print("\n=== Verificando com SQLAlchemy Inspector ===")
inspector = inspect(engine)
print(f"Schemas: {inspector.get_schema_names()}")
print(f"Tabelas em 'core': {inspector.get_table_names(schema='core')}")

print("\n=== Testando import do Model ===")
try:
    from app.models.order import Order
    print(f"✓ Model Order importado")
    print(f"  __tablename__: {Order.__tablename__}")
    print(f"  __table_args__: {Order.__table_args__}")
except Exception as e:
    print(f"✗ Erro ao importar Order: {e}")

print("\n=== Testando query com SQLAlchemy ORM ===")
from sqlalchemy.orm import sessionmaker
from app.models.order import Order

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    count = db.query(Order).count()
    print(f"✓ db.query(Order).count() = {count}")
    
    orders = db.query(Order).limit(3).all()
    print(f"✓ Primeiras {len(orders)} orders:")
    for order in orders:
        print(f"  - {order.id}: {order.description} (R$ {order.total})")
except Exception as e:
    print(f"✗ Erro na query ORM: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n=== FIM DO TESTE ===")

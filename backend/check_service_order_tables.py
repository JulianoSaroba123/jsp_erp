"""
Verifica se as tabelas de service_order existem no banco.
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect

# Configurar PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

# Database URL do .env
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL não configurada no .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL, echo=False)

print("=" * 60)
print("VERIFICANDO TABELAS DE SERVICE ORDERS NO SCHEMA core")
print("=" * 60)

with engine.connect() as conn:
    # Verificar tabelas no schema core
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'core' 
        AND table_name LIKE '%service_order%'
        ORDER BY table_name
    """))
    
    tables = [row[0] for row in result]
    
    if tables:
        print(f"✅ Encontradas {len(tables)} tabelas de service_order:")
        for table in tables:
            print(f"   - core.{table}")
    else:
        print("❌ NENHUMA tabela de service_order encontrada no schema core")
    
    print("\n" + "=" * 60)
    print("VERIFICANDO ESTRUTURA DAS TABELAS")
    print("=" * 60)
    
    expected_tables = [
        'service_orders',
        'service_order_items',
        'service_order_products',
        'service_order_installments',
        'service_order_attachments'
    ]
    
    for table_name in expected_tables:
        if table_name in tables:
            result = conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'core' AND table_name = '{table_name}'
                ORDER BY ordinal_position
            """))
            
            print(f"\n✅ core.{table_name}:")
            for row in result:
                nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
                print(f"   - {row[0]}: {row[1]} {nullable}")
        else:
            print(f"\n❌ core.{table_name}: NÃO EXISTE")
    
    # Verificar versão do Alembic
    print("\n" + "=" * 60)
    print("VERIFICANDO VERSÃO DO ALEMBIC")
    print("=" * 60)
    
    result = conn.execute(text("""
        SELECT version_num FROM core.alembic_version
    """))
    
    version = result.scalar()
    print(f"Versão atual: {version}")

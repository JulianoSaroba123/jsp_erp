"""
Auditoria completa do banco de dados - Service Orders.
"""
import os
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/erp_jsp_db')

print("=" * 80)
print("AUDITORIA DE BANCO DE DADOS - SERVICE ORDERS")
print("=" * 80)

try:
    engine = create_engine(DATABASE_URL)
    
    # 1. Verificar tabelas
    print("\n1️⃣ Tabelas relacionadas a Service Orders:")
    print("-" * 80)
    
    inspector = inspect(engine)
    all_tables = inspector.get_table_names(schema='core')
    so_tables = [t for t in all_tables if 'service_order' in t]
    
    if so_tables:
        for table in sorted(so_tables):
            print(f"   ✅ core.{table}")
            
            # Verificar colunas
            columns = inspector.get_columns(table, schema='core')
            print(f"      Colunas: {len(columns)}")
            
            # Verificar FKs
            fks = inspector.get_foreign_keys(table, schema='core')
            if fks:
                print(f"      Foreign Keys: {len(fks)}")
                for fk in fks:
                    print(f"         - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            
            # Verificar índices
            indexes = inspector.get_indexes(table, schema='core')
            if indexes:
                print(f"      Índices: {len(indexes)}")
            
            print()
    else:
        print("   ❌ Nenhuma tabela service_order encontrada!")
    
    # 2. Verificar alembic_version
    print("\n2️⃣ Versão atual do Alembic:")
    print("-" * 80)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"   📌 Versão atual: {version}")
    
    # 3. Contar registros
    print("\n3️⃣ Registros nas tabelas:")
    print("-" * 80)
    
    with engine.connect() as conn:
        for table in sorted(so_tables):
            result = conn.execute(text(f'SELECT COUNT(*) FROM core.{table}'))
            count = result.scalar()
            print(f"   core.{table}: {count} registro(s)")
    
    print("\n" + "=" * 80)
    print("✅ AUDITORIA CONCLUÍDA")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

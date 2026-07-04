"""
Script para criar tabelas de Service Orders manualmente
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))

# Ler script SQL
with open('create_service_orders_tables.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Executar
try:
    with engine.connect() as conn:
        # Executar cada statement separadamente
        statements = sql_script.split(';')
        for statement in statements:
            clean_stmt = statement.strip()
            if clean_stmt and not clean_stmt.startswith('--'):
                try:
                    result = conn.execute(text(clean_stmt))
                    conn.commit()
                    # Se houver resultado, imprimir
                    try:
                        row = result.fetchone()
                        if row:
                            print(row[0])
                    except:
                        pass
                except Exception as e:
                    error_msg = str(e)
                    # Ignorar erros de "já existe"
                    if 'already exists' in error_msg or 'já existe' in error_msg:
                        print(f"⚠️  Ignorando: {clean_stmt[:50]}... (já existe)")
                    else:
                        print(f"❌ Erro: {e}")
                        raise
    
    print("\n" + "="*80)
    print("✅ SUCESSO! Tabelas de Service Orders criadas")
    print("="*80)
    
    # Verificar tabelas criadas
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'core' 
            AND table_name LIKE 'service_order%'
            ORDER BY table_name
        """))
        
        print("\nTabelas criadas:")
        for row in result:
            print(f"  ✓ {row[0]}")
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    sys.exit(1)

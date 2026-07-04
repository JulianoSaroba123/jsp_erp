"""Check if products table exists"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # Check if table exists
    result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='core' AND table_name='products'
    """)).fetchall()
    
    print(f"✅ Tabela products existe: {len(result) > 0}")
    
    if len(result) > 0:
        # Check columns
        columns = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema='core' AND table_name='products'
            ORDER BY ordinal_position
        """)).fetchall()
        
        print(f"\n📋 Colunas atuais ({len(columns)}):")
        for col in columns:
            print(f"  - {col[0]}")
    else:
        print("\n❌ Tabela não existe! Precisamos rodar migração 008 primeiro.")
        
finally:
    db.close()

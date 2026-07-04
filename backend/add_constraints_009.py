"""Add constraints for migration 009"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("🔧 Adicionando constraints...\n")
    
    constraints = [
        ("check_product_peso_positive", "peso IS NULL OR peso >= 0"),
        ("check_product_markup_valid", "markup IS NULL OR (markup >= 0 AND markup <= 1000)"),
        ("check_product_margem_lucro_valid", "margem_lucro IS NULL OR (margem_lucro >= -100 AND margem_lucro <= 1000)"),
        ("check_product_estoque_maximo_positive", "estoque_maximo IS NULL OR estoque_maximo >= 0")
    ]
    
    try:
        for constraint_name, check_condition in constraints:
            # Check if constraint exists
            exists = conn.execute(text(f"""
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_schema = 'core' 
                AND table_name = 'products' 
                AND constraint_name = '{constraint_name}'
            """)).fetchone()
            
            if not exists:
                conn.execute(text(f"""
                    ALTER TABLE core.products 
                    ADD CONSTRAINT {constraint_name} 
                    CHECK ({check_condition})
                """))
                print(f"✅ {constraint_name}")
            else:
                print(f"⏭️  {constraint_name} (já existe)")
        
        conn.commit()
        
        # Update alembic version
        conn.execute(text("UPDATE core.alembic_version SET version_num = '009_extend_products'"))
        conn.commit()
        
        print("\n✅ Migration 009 totalmente aplicada!")
        print("✅ Versão atualizada para 009_extend_products")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro: {e}")
        raise

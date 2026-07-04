"""Apply migration 009 manually"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("🔧 Aplicando migration 009 manualmente...\n")
    
    try:
        # Identificação Estendida
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS codigo_barras VARCHAR(50)"))
        print("✅ codigo_barras")
        
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS marca VARCHAR(100)"))
        print("✅ marca")
        
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS modelo VARCHAR(100)"))
        print("✅ modelo")
        
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS subcategoria VARCHAR(80)"))
        print("✅ subcategoria")
        
        # Características Físicas
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS peso NUMERIC(10,3)"))
        print("✅ peso")
        
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS dimensoes VARCHAR(100)"))
        print("✅ dimensoes")
        
        # Gestão de Preços
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS markup NUMERIC(5,2)"))
        print("✅ markup")
        
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS margem_lucro NUMERIC(5,2)"))
        print("✅ margem_lucro")
        
        # Gestão de Estoque
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS estoque_maximo NUMERIC(12,3)"))
        print("✅ estoque_maximo")
        
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS controla_estoque BOOLEAN DEFAULT TRUE"))
        print("✅ controla_estoque")
        
        # Relacionamentos
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS fornecedor_id UUID"))
        print("✅ fornecedor_id")
        
        # Observações
        conn.execute(text("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS observacoes TEXT"))
        print("✅ observacoes")
        
        # Índice único para codigo_barras
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_products_codigo_barras_unique 
            ON core.products (codigo_barras) 
            WHERE codigo_barras IS NOT NULL AND deleted_at IS NULL
        """))
        print("✅ idx_products_codigo_barras_unique")
        
        # Índices
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_marca ON core.products (marca)"))
        print("✅ idx_products_marca")
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_subcategoria ON core.products (subcategoria)"))
        print("✅ idx_products_subcategoria")
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_user_subcategoria ON core.products (user_id, subcategoria)"))
        print("✅ idx_products_user_subcategoria")
        
        # Check Constraints
        conn.execute(text("""
            ALTER TABLE core.products 
            ADD CONSTRAINT IF NOT EXISTS check_product_peso_positive 
            CHECK (peso IS NULL OR peso >= 0)
        """))
        print("✅ check_product_peso_positive")
        
        conn.execute(text("""
            ALTER TABLE core.products 
            ADD CONSTRAINT IF NOT EXISTS check_product_markup_valid 
            CHECK (markup IS NULL OR (markup >= 0 AND markup <= 1000))
        """))
        print("✅ check_product_markup_valid")
        
        conn.execute(text("""
            ALTER TABLE core.products 
            ADD CONSTRAINT IF NOT EXISTS check_product_margem_lucro_valid 
            CHECK (margem_lucro IS NULL OR (margem_lucro >= -100 AND margem_lucro <= 1000))
        """))
        print("✅ check_product_margem_lucro_valid")
        
        conn.execute(text("""
            ALTER TABLE core.products 
            ADD CONSTRAINT IF NOT EXISTS check_product_estoque_maximo_positive 
            CHECK (estoque_maximo IS NULL OR estoque_maximo >= 0)
        """))
        print("✅ check_product_estoque_maximo_positive")
        
        conn.commit()
        
        print("\n✅ Migration 009 aplicada com sucesso!")
        
        # Update alembic version
        conn.execute(text("UPDATE core.alembic_version SET version_num = '009_extend_products'"))
        conn.commit()
        
        print("✅ Versão atualizada para 009_extend_products")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro: {e}")
        raise

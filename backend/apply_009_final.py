"""Apply migration 009 - columns and indexes only"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("🔧 Aplicando colunas da migration 009...\n")
    
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
    
    conn.commit()
    print("\n✅ Todas as colunas adicionadas!")
    
    # Índices
    print("\n🔧 Criando índices...\n")
    
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_products_codigo_barras_unique 
        ON core.products (codigo_barras) 
        WHERE codigo_barras IS NOT NULL AND deleted_at IS NULL
    """))
    print("✅ idx_products_codigo_barras_unique")
    
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_marca ON core.products (marca)"))
    print("✅ idx_products_marca")
    
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_subcategoria ON core.products (subcategoria)"))
    print("✅ idx_products_subcategoria")
    
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_user_subcategoria ON core.products (user_id, subcategoria)"))
    print("✅ idx_products_user_subcategoria")
    
    conn.commit()
    print("\n✅ Todos os índices criados!")
    
    # Update alembic version
    conn.execute(text("UPDATE core.alembic_version SET version_num = '009_extend_products'"))
    conn.commit()
    
    print("\n✅ Migration 009 aplicada!")
    print("✅ Versão atualizada para 009_extend_products")

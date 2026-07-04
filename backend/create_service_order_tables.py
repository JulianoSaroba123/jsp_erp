"""
Script para criar manualmente as tabelas service_order_* que faltam no banco.
Executar apenas se alembic upgrade falhar.
"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("🔍 Verificando tabelas existentes...")
    
    result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='core' 
        AND table_name LIKE 'service_order%'
        ORDER BY table_name
    """)).fetchall()
    
    existing_tables = [row[0] for row in result]
    print(f"✅ Tabelas encontradas: {existing_tables}")
    
    required_tables = [
        'service_orders',
        'service_order_items',
        'service_order_products',
        'service_order_installments',
        'service_order_attachments'
    ]
    
    missing_tables = [t for t in required_tables if t not in existing_tables]
    
    if not missing_tables:
        print("✅ Todas as tabelas já existem!")
        db.close()
        exit(0)
    
    print(f"\n⚠️  Tabelas faltando: {missing_tables}")
    print("\n🔧 Criando tabelas manualmente...\n")
    
    # ==================== SERVICE_ORDER_ITEMS ====================
    if 'service_order_items' in missing_tables:
        print("Criando: core.service_order_items")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS core.service_order_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
                description VARCHAR(200) NOT NULL,
                service_type VARCHAR(20) NOT NULL DEFAULT 'hora',
                quantity NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
                unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            );
            
            CREATE INDEX IF NOT EXISTS ix_service_order_items_service_order_id 
            ON core.service_order_items(service_order_id);
            
            COMMENT ON TABLE core.service_order_items IS 'Serviços realizados na ordem de serviço';
            COMMENT ON COLUMN core.service_order_items.service_type IS 'Tipo: hora, dia, fechado';
        """))
        print("  ✅ service_order_items criada")
    
    # ==================== SERVICE_ORDER_PRODUCTS ====================
    if 'service_order_products' in missing_tables:
        print("Criando: core.service_order_products")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS core.service_order_products (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
                product_id UUID REFERENCES core.products(id) ON DELETE SET NULL,
                description VARCHAR(200) NOT NULL,
                quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00,
                unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            );
            
            CREATE INDEX IF NOT EXISTS ix_service_order_products_service_order_id 
            ON core.service_order_products(service_order_id);
            
            CREATE INDEX IF NOT EXISTS ix_service_order_products_product_id 
            ON core.service_order_products(product_id);
            
            COMMENT ON TABLE core.service_order_products IS 'Produtos/peças utilizados na OS';
        """))
        print("  ✅ service_order_products criada")
    
    # ==================== SERVICE_ORDER_INSTALLMENTS ====================
    if 'service_order_installments' in missing_tables:
        print("Criando: core.service_order_installments")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS core.service_order_installments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
                installment_number INTEGER NOT NULL,
                due_date DATE NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                paid BOOLEAN NOT NULL DEFAULT FALSE,
                payment_date DATE,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            );
            
            CREATE INDEX IF NOT EXISTS ix_service_order_installments_service_order_id 
            ON core.service_order_installments(service_order_id);
            
            COMMENT ON TABLE core.service_order_installments IS 'Parcelas de pagamento da OS';
        """))
        print("  ✅ service_order_installments criada")
    
    # ==================== SERVICE_ORDER_ATTACHMENTS ====================
    if 'service_order_attachments' in missing_tables:
        print("Criando: core.service_order_attachments")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS core.service_order_attachments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500),
                file_size INTEGER,
                mime_type VARCHAR(100),
                file_data BYTEA,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                uploaded_by UUID REFERENCES core.users(id)
            );
            
            CREATE INDEX IF NOT EXISTS ix_service_order_attachments_service_order_id 
            ON core.service_order_attachments(service_order_id);
            
            COMMENT ON TABLE core.service_order_attachments IS 'Anexos da OS (fotos, PDFs, etc)';
        """))
        print("  ✅ service_order_attachments criada")
    
    db.commit()
    
    # Verificar novamente
    result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='core' 
        AND table_name LIKE 'service_order%'
        ORDER BY table_name
    """)).fetchall()
    
    final_tables = [row[0] for row in result]
    print(f"\n✅ Tabelas finais: {final_tables}")
    
    print("\n🎉 Todas as tabelas foram criadas com sucesso!")
    
except Exception as e:
    db.rollback()
    print(f"\n❌ Erro: {e}")
    raise
finally:
    db.close()

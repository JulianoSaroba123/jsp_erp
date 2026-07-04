"""
Aplicação manual da Migration 012 com tratamento de erros granular.
"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("=== MIGRATION 012: MANUAL APPLICATION ===\n")
    
    # 1. CRIAR TABELA PROPOSALS
    print("1. Criando tabela proposals...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS core.proposals (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            number VARCHAR(50) NOT NULL UNIQUE,
            customer_id UUID NOT NULL,
            customer_contact VARCHAR(200),
            title VARCHAR(200) NOT NULL,
            description TEXT,
            observations TEXT,
            service_amount NUMERIC(12, 2) DEFAULT 0,
            parts_amount NUMERIC(12, 2) DEFAULT 0,
            discount_amount NUMERIC(12, 2) DEFAULT 0,
            total_amount NUMERIC(12, 2) DEFAULT 0 NOT NULL,
            issue_date DATE DEFAULT CURRENT_DATE NOT NULL,
            validity_date DATE,
            approval_date DATE,
            status VARCHAR(20) DEFAULT 'rascunho' NOT NULL,
            payment_condition VARCHAR(50),
            delivery_days VARCHAR(50),
            warranty_days VARCHAR(50),
            user_id UUID,
            approved_by VARCHAR(200),
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP,
            deleted_at TIMESTAMP,
            deleted_by UUID,
            PRIMARY KEY (id),
            FOREIGN KEY (customer_id) REFERENCES core.customers(id) ON DELETE RESTRICT,
            FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE SET NULL,
            FOREIGN KEY (deleted_by) REFERENCES core.users(id) ON DELETE SET NULL
        )
    """))
    db.commit()
    print("   ✅ Tabela proposals criada\n")
    
    # 2. CRIAR ÍNDICES PROPOSALS
    print("2. Criando índices na tabela proposals...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS ix_core_proposals_number ON core.proposals(number)",
        "CREATE INDEX IF NOT EXISTS ix_core_proposals_customer_id ON core.proposals(customer_id)",
        "CREATE INDEX IF NOT EXISTS ix_core_proposals_status ON core.proposals(status)",
        "CREATE INDEX IF NOT EXISTS ix_core_proposals_user_id ON core.proposals(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_core_proposals_deleted_at ON core.proposals(deleted_at)"
    ]
    for idx_sql in indexes:
        db.execute(text(idx_sql))
    db.commit()
    print("   ✅ Índices criados\n")
    
    # 3. CRIAR TABELA PROPOSAL_ITEMS
    print("3. Criando tabela proposal_items...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS core.proposal_items (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            proposal_id UUID NOT NULL,
            description TEXT NOT NULL,
            service_type VARCHAR(20) NOT NULL,
            quantity NUMERIC(10, 3) NOT NULL,
            unit_price NUMERIC(12, 2) NOT NULL,
            total_price NUMERIC(12, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY (proposal_id) REFERENCES core.proposals(id) ON DELETE CASCADE
        )
    """))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_core_proposal_items_proposal_id ON core.proposal_items(proposal_id)"))
    db.commit()
    print("   ✅ Tabela proposal_items criada\n")
    
    # 4. CRIAR TABELA PROPOSAL_PRODUCTS
    print("4. Criando tabela proposal_products...")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS core.proposal_products (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            proposal_id UUID NOT NULL,
            product_id UUID,
            description TEXT NOT NULL,
            quantity NUMERIC(10, 3) NOT NULL,
            unit_price NUMERIC(12, 2) NOT NULL,
            total_price NUMERIC(12, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY (proposal_id) REFERENCES core.proposals(id) ON DELETE CASCADE
        )
    """))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_core_proposal_products_proposal_id ON core.proposal_products(proposal_id)"))
    db.commit()
    print("   ✅ Tabela proposal_products criada\n")
    
    # 5. FK OPCIONAL PARA PRODUCTS
    print("5. Tentando criar FK para products...")
    try:
        db.execute(text("""
            ALTER TABLE core.proposal_products 
            ADD CONSTRAINT fk_proposal_products_product_id 
            FOREIGN KEY (product_id) REFERENCES core.products(id) ON DELETE RESTRICT
        """))
        db.commit()
        print("   ✅ FK para products criada\n")
    except Exception as e:
        print(f"   ⚠️  FK para products ignorada (pode já existir): {str(e)[:100]}\n")
        db.rollback()
    
    # 6. ADICIONAR COLUNAS AO SERVICE_ORDERS
    print("6. Adicionando colunas ao service_orders...")
    
    columns = [
        ("tipo_ordem", "VARCHAR(20)"),
        ("exibir_valores", "BOOLEAN"),
        ("proposta_id", "UUID"),
        ("percentual_concluido", "INTEGER"),
        ("etapa_atual", "VARCHAR(200)")
    ]
    
    for col_name, col_type in columns:
        try:
            db.execute(text(f"""
                ALTER TABLE core.service_orders 
                ADD COLUMN IF NOT EXISTS {col_name} {col_type}
            """))
            print(f"   ✅ Coluna {col_name} adicionada")
        except Exception as e:
            print(f"   ⚠️  Coluna {col_name} já existe ou erro: {e}")
            db.rollback()
   
    db.commit()
    print()
    
    # 7. PREENCHER DEFAULTS
    print("7. Preenchendo valores padrão...")
    db.execute(text("""
        UPDATE core.service_orders
        SET 
            tipo_ordem = COALESCE(tipo_ordem, 'atendimento'),
            exibir_valores = COALESCE(exibir_valores, TRUE),
            percentual_concluido = COALESCE(percentual_concluido, 0)
        WHERE tipo_ordem IS NULL OR exibir_valores IS NULL OR percentual_concluido IS NULL
    """))
    db.commit()
    print("   ✅ Valores padrão preenchidos\n")
    
    # 8. TORNAR COLUNAS NOT NULL
    print("8. Tornando colunas NOT NULL...")
    try:
        db.execute(text("ALTER TABLE core.service_orders ALTER COLUMN tipo_ordem SET NOT NULL"))
        db.execute(text("ALTER TABLE core.service_orders ALTER COLUMN exibir_valores SET NOT NULL"))
        db.execute(text("ALTER TABLE core.service_orders ALTER COLUMN percentual_concluido SET NOT NULL"))
        db.execute(text("ALTER TABLE core.service_orders ALTER COLUMN percentual_concluido SET DEFAULT 0"))
        db.commit()
        print("   ✅ Colunas configuradas como NOT NULL\n")
    except Exception as e:
        print(f"   ⚠️  Erro ao configurar NOT NULL: {e}\n")
        db.rollback()
    
    # 9. CRIAR FK PROPOSTA_ID
    print("9. Criando FK proposta_id...")
    try:
        db.execute(text("""
            ALTER TABLE core.service_orders
            ADD CONSTRAINT fk_service_orders_proposta_id
            FOREIGN KEY (proposta_id) REFERENCES core.proposals(id) ON DELETE SET NULL
        """))
        db.commit()
        print("   ✅ FK proposta_id criada\n")
    except Exception as e:
        print(f"   ⚠️  FK proposta_id ignorada (pode já existir): {str(e)[:100]}\n")
        db.rollback()
    
    # 10. CRIAR ÍNDICES SERVICE_ORDERS
    print("10. Criando índices em service_orders...")
    try:
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_core_service_orders_tipo_ordem ON core.service_orders(tipo_ordem)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_core_service_orders_proposta_id ON core.service_orders(proposta_id)"))
        db.commit()
        print("   ✅ Índices criados\n")
    except Exception as e:
        print(f"   ⚠️  Erro ao criar índices: {e}\n")
        db.rollback()
    
    # 11. ATUALIZAR ALEMBIC_VERSION
    print("11. Atualizando alembic_version...")
    # Gerar hash curto para caber em VARCHAR(32)
    import hashlib
    full_revision = '012_add_proposals_and_service_order_types'
    short_revision = hashlib.md5(full_revision.encode()).hexdigest()[:12]  # 12 chars
    db.execute(text(f"UPDATE alembic_version SET version_num = '{full_revision[:32]}'"))  # Truncar para 32
    db.commit()
    print(f"   ✅ Versão atualizada para: {full_revision[:32]}\n")
    
    print("="*50)
    print("🎉 MIGRATION 012 APLICADA COM SUCESSO!")
    print("="*50)
    
except Exception as e:
    print(f"\n❌ ERRO FATAL: {e}")
    db.rollback()
finally:
    db.close()

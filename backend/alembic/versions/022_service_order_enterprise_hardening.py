"""service order enterprise hardening

Revision ID: 022_service_order_enterprise_hardening
Revises: 021_set_service_order_legacy_defaults
Create Date: 2026-05-27
"""

from alembic import op


revision = "022_service_order_enterprise_hardening"
down_revision = "021_set_service_order_legacy_defaults"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS code VARCHAR(20)")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS technical_report TEXT")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS observations TEXT")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS client_name VARCHAR(200)")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS client_document VARCHAR(30)")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS client_phone VARCHAR(30)")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS client_email VARCHAR(255)")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS client_address TEXT")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50)")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS total_services NUMERIC(10,2) DEFAULT 0")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS total_products NUMERIC(10,2) DEFAULT 0")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS total_displacement NUMERIC(10,2) DEFAULT 0")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS total_discount NUMERIC(10,2) DEFAULT 0")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS total_amount_enterprise NUMERIC(10,2) DEFAULT 0")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS started_at TIMESTAMP")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP")

    op.execute("ALTER TABLE core.service_order_items ADD COLUMN IF NOT EXISTS unit VARCHAR(20) DEFAULT 'un'")
    op.execute("ALTER TABLE core.service_order_items ADD COLUMN IF NOT EXISTS technician_notes TEXT")

    op.execute("ALTER TABLE core.service_order_products ADD COLUMN IF NOT EXISTS product_name VARCHAR(200)")

    op.execute("ALTER TABLE core.service_order_installments ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending'")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS core.service_order_equipments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
            equipment_name VARCHAR(200) NOT NULL,
            brand VARCHAR(100),
            model VARCHAR(100),
            serial_number VARCHAR(100),
            accessories TEXT,
            defect_reported TEXT,
            technical_diagnosis TEXT,
            created_at TIMESTAMP DEFAULT now()
        )
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_service_order_equipments_service_order_id "
        "ON core.service_order_equipments(service_order_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_service_orders_code_unique "
        "ON core.service_orders(code) WHERE code IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_financial_entries_service_order_id_not_deleted "
        "ON core.financial_entries(service_order_id) "
        "WHERE service_order_id IS NOT NULL AND deleted_at IS NULL"
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'core'
                  AND table_name = 'audit_logs'
                  AND column_name = 'entity_type'
            ) THEN
                ALTER TABLE core.audit_logs DROP CONSTRAINT IF EXISTS check_audit_entity_type;
                ALTER TABLE core.audit_logs
                    ADD CONSTRAINT check_audit_entity_type
                    CHECK (entity_type IN ('order', 'financial_entry', 'user', 'service_order'));
            ELSIF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'core'
                  AND table_name = 'audit_logs'
                  AND column_name = 'resource_type'
            ) THEN
                ALTER TABLE core.audit_logs DROP CONSTRAINT IF EXISTS check_audit_resource_type;
                ALTER TABLE core.audit_logs
                    ADD CONSTRAINT check_audit_resource_type
                    CHECK (resource_type IN ('order', 'financial_entry', 'user', 'service_order'));
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS core.uq_financial_entries_service_order_id_not_deleted")
    op.execute("DROP INDEX IF EXISTS core.ix_service_orders_code_unique")
    op.execute("DROP INDEX IF EXISTS core.ix_service_order_equipments_service_order_id")
    op.execute("DROP TABLE IF EXISTS core.service_order_equipments")

    op.execute("ALTER TABLE core.service_order_installments DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE core.service_order_products DROP COLUMN IF EXISTS product_name")
    op.execute("ALTER TABLE core.service_order_items DROP COLUMN IF EXISTS technician_notes")
    op.execute("ALTER TABLE core.service_order_items DROP COLUMN IF EXISTS unit")

    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS completed_at")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS started_at")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS total_amount_enterprise")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS total_discount")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS total_displacement")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS total_products")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS total_services")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS payment_method")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS client_address")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS client_email")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS client_phone")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS client_document")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS client_name")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS observations")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS technical_report")
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS code")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'core'
                  AND table_name = 'audit_logs'
                  AND column_name = 'entity_type'
            ) THEN
                ALTER TABLE core.audit_logs DROP CONSTRAINT IF EXISTS check_audit_entity_type;
                ALTER TABLE core.audit_logs
                    ADD CONSTRAINT check_audit_entity_type
                    CHECK (entity_type IN ('order', 'financial_entry', 'user'));
            ELSIF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'core'
                  AND table_name = 'audit_logs'
                  AND column_name = 'resource_type'
            ) THEN
                ALTER TABLE core.audit_logs DROP CONSTRAINT IF EXISTS check_audit_resource_type;
                ALTER TABLE core.audit_logs
                    ADD CONSTRAINT check_audit_resource_type
                    CHECK (resource_type IN ('order', 'financial_entry', 'user'));
            END IF;
        END $$;
        """
    )

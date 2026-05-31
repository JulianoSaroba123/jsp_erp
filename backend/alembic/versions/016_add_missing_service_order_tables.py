"""016 - Add missing service order related tables

Revision ID: 016_add_missing_service_order_tables
Revises: 015_enhance_service_orders
Create Date: 2026-05-12 12:00:00
"""
from alembic import op


revision = "016_add_missing_service_order_tables"
down_revision = "015_enhance_service_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    connection.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS core.service_order_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
            description VARCHAR(200) NOT NULL,
            service_type VARCHAR(20) NOT NULL DEFAULT 'hora',
            quantity NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
            unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    connection.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS core.service_order_products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
            product_id UUID,
            description VARCHAR(200) NOT NULL,
            quantity NUMERIC(10, 3) NOT NULL DEFAULT 1.000,
            unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            total_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    connection.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS core.service_order_installments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
            installment_number INTEGER NOT NULL,
            due_date DATE NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            paid BOOLEAN NOT NULL DEFAULT false,
            payment_date DATE,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    connection.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS core.service_order_attachments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            service_order_id UUID NOT NULL REFERENCES core.service_orders(id) ON DELETE CASCADE,
            original_filename VARCHAR(255) NOT NULL,
            stored_filename VARCHAR(255) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            mime_type VARCHAR(100),
            file_size INTEGER,
            file_path VARCHAR(500),
            file_content BYTEA,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_service_order_items_service_order_id
            ON core.service_order_items(service_order_id)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_service_order_products_service_order_id
            ON core.service_order_products(service_order_id)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_service_order_products_product_id
            ON core.service_order_products(product_id)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_service_order_installments_service_order_id
            ON core.service_order_installments(service_order_id)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_service_order_installments_due_date
            ON core.service_order_installments(due_date)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_service_order_attachments_service_order_id
            ON core.service_order_attachments(service_order_id)
    """)

    connection.exec_driver_sql("""
        DO $$
        BEGIN
            IF to_regclass('core.products') IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1 FROM pg_constraint
                   WHERE conname = 'fk_service_order_products_product_id'
               ) THEN
                ALTER TABLE core.service_order_products
                    ADD CONSTRAINT fk_service_order_products_product_id
                    FOREIGN KEY (product_id)
                    REFERENCES core.products(id)
                    ON DELETE SET NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    connection = op.get_bind()
    connection.exec_driver_sql("DROP TABLE IF EXISTS core.service_order_attachments CASCADE")
    connection.exec_driver_sql("DROP TABLE IF EXISTS core.service_order_installments CASCADE")
    connection.exec_driver_sql("DROP TABLE IF EXISTS core.service_order_products CASCADE")
    connection.exec_driver_sql("DROP TABLE IF EXISTS core.service_order_items CASCADE")

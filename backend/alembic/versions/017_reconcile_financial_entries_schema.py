"""017 - Reconcile financial entries schema

Revision ID: 017_reconcile_financial
Revises: 016_add_missing_service_order_tables
Create Date: 2026-05-16 19:15:00

This migration repairs databases that were stamped at head while missing the
professional financial_entries columns introduced in revision 014.
"""
from alembic import op


revision = "017_reconcile_financial"
down_revision = "016_add_missing_service_order_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    connection.exec_driver_sql("""
        ALTER TABLE core.financial_entries
            ADD COLUMN IF NOT EXISTS category VARCHAR(100),
            ADD COLUMN IF NOT EXISTS subcategory VARCHAR(100),
            ADD COLUMN IF NOT EXISTS due_date TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS payment_date TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS document_number VARCHAR(50),
            ADD COLUMN IF NOT EXISTS document_type VARCHAR(30),
            ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50),
            ADD COLUMN IF NOT EXISTS notes TEXT,
            ADD COLUMN IF NOT EXISTS customer_id UUID,
            ADD COLUMN IF NOT EXISTS supplier_id UUID,
            ADD COLUMN IF NOT EXISTS service_order_id UUID,
            ADD COLUMN IF NOT EXISTS original_amount NUMERIC(12, 2),
            ADD COLUMN IF NOT EXISTS interest NUMERIC(12, 2) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS discount NUMERIC(12, 2) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS penalty NUMERIC(12, 2) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS installment_info VARCHAR(20),
            ADD COLUMN IF NOT EXISTS is_recurring BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN IF NOT EXISTS recurrence_frequency VARCHAR(20),
            ADD COLUMN IF NOT EXISTS origin VARCHAR(50) NOT NULL DEFAULT 'MANUAL'
    """)

    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_financial_entries_category
            ON core.financial_entries(category)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_financial_entries_due_date
            ON core.financial_entries(due_date)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_financial_entries_payment_date
            ON core.financial_entries(payment_date)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_financial_entries_customer_id
            ON core.financial_entries(customer_id)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_financial_entries_supplier_id
            ON core.financial_entries(supplier_id)
    """)
    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_financial_entries_service_order_id
            ON core.financial_entries(service_order_id)
    """)

    connection.exec_driver_sql("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_financial_entries_customer'
            ) THEN
                ALTER TABLE core.financial_entries
                    ADD CONSTRAINT fk_financial_entries_customer
                    FOREIGN KEY (customer_id)
                    REFERENCES core.customers(id)
                    ON DELETE SET NULL;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_financial_entries_supplier'
            ) THEN
                ALTER TABLE core.financial_entries
                    ADD CONSTRAINT fk_financial_entries_supplier
                    FOREIGN KEY (supplier_id)
                    REFERENCES core.suppliers(id)
                    ON DELETE SET NULL;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_financial_entries_service_order'
            ) THEN
                ALTER TABLE core.financial_entries
                    ADD CONSTRAINT fk_financial_entries_service_order
                    FOREIGN KEY (service_order_id)
                    REFERENCES core.service_orders(id)
                    ON DELETE SET NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    connection = op.get_bind()

    connection.exec_driver_sql("ALTER TABLE core.financial_entries DROP CONSTRAINT IF EXISTS fk_financial_entries_service_order")
    connection.exec_driver_sql("ALTER TABLE core.financial_entries DROP CONSTRAINT IF EXISTS fk_financial_entries_supplier")
    connection.exec_driver_sql("ALTER TABLE core.financial_entries DROP CONSTRAINT IF EXISTS fk_financial_entries_customer")

    connection.exec_driver_sql("DROP INDEX IF EXISTS core.ix_financial_entries_service_order_id")
    connection.exec_driver_sql("DROP INDEX IF EXISTS core.ix_financial_entries_supplier_id")
    connection.exec_driver_sql("DROP INDEX IF EXISTS core.ix_financial_entries_customer_id")
    connection.exec_driver_sql("DROP INDEX IF EXISTS core.ix_financial_entries_payment_date")
    connection.exec_driver_sql("DROP INDEX IF EXISTS core.ix_financial_entries_due_date")
    connection.exec_driver_sql("DROP INDEX IF EXISTS core.ix_financial_entries_category")

    connection.exec_driver_sql("""
        ALTER TABLE core.financial_entries
            DROP COLUMN IF EXISTS origin,
            DROP COLUMN IF EXISTS recurrence_frequency,
            DROP COLUMN IF EXISTS is_recurring,
            DROP COLUMN IF EXISTS installment_info,
            DROP COLUMN IF EXISTS penalty,
            DROP COLUMN IF EXISTS discount,
            DROP COLUMN IF EXISTS interest,
            DROP COLUMN IF EXISTS original_amount,
            DROP COLUMN IF EXISTS service_order_id,
            DROP COLUMN IF EXISTS supplier_id,
            DROP COLUMN IF EXISTS customer_id,
            DROP COLUMN IF EXISTS notes,
            DROP COLUMN IF EXISTS payment_method,
            DROP COLUMN IF EXISTS document_type,
            DROP COLUMN IF EXISTS document_number,
            DROP COLUMN IF EXISTS payment_date,
            DROP COLUMN IF EXISTS due_date,
            DROP COLUMN IF EXISTS subcategory,
            DROP COLUMN IF EXISTS category
    """)

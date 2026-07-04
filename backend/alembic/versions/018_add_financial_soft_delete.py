"""018 - Add financial entries soft delete columns

Revision ID: 018_add_financial_soft_delete
Revises: 017_reconcile_financial
Create Date: 2026-05-16 19:35:00
"""
from alembic import op


revision = "018_add_financial_soft_delete"
down_revision = "017_reconcile_financial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    connection.exec_driver_sql("""
        ALTER TABLE core.financial_entries
            ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS deleted_by UUID
    """)

    connection.exec_driver_sql("""
        CREATE INDEX IF NOT EXISTS ix_financial_entries_deleted_at
            ON core.financial_entries(deleted_at)
    """)

    connection.exec_driver_sql("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_financial_entries_deleted_by'
            ) THEN
                ALTER TABLE core.financial_entries
                    ADD CONSTRAINT fk_financial_entries_deleted_by
                    FOREIGN KEY (deleted_by)
                    REFERENCES core.users(id)
                    ON DELETE SET NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    connection = op.get_bind()
    connection.exec_driver_sql("ALTER TABLE core.financial_entries DROP CONSTRAINT IF EXISTS fk_financial_entries_deleted_by")
    connection.exec_driver_sql("DROP INDEX IF EXISTS core.ix_financial_entries_deleted_at")
    connection.exec_driver_sql("""
        ALTER TABLE core.financial_entries
            DROP COLUMN IF EXISTS deleted_by,
            DROP COLUMN IF EXISTS deleted_at
    """)

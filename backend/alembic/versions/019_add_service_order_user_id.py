"""add user_id to service_orders

Revision ID: 019_add_service_order_user_id
Revises: 018_add_financial_soft_delete
Create Date: 2026-05-17
"""

from alembic import op


revision = "019_add_service_order_user_id"
down_revision = "018_add_financial_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS user_id UUID")
    op.execute(
        """
        UPDATE core.service_orders
        SET user_id = (SELECT id FROM core.users ORDER BY created_at ASC LIMIT 1)
        WHERE user_id IS NULL
          AND EXISTS (SELECT 1 FROM core.users)
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM core.service_orders WHERE user_id IS NULL)
               AND NOT EXISTS (SELECT 1 FROM core.users) THEN
                RAISE EXCEPTION 'Cannot backfill core.service_orders.user_id: no users found';
            END IF;

            IF NOT EXISTS (SELECT 1 FROM core.service_orders WHERE user_id IS NULL) THEN
                ALTER TABLE core.service_orders ALTER COLUMN user_id SET NOT NULL;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_service_orders_user_id'
                  AND conrelid = 'core.service_orders'::regclass
            ) THEN
                ALTER TABLE core.service_orders
                ADD CONSTRAINT fk_service_orders_user_id
                FOREIGN KEY (user_id) REFERENCES core.users(id);
            END IF;
        END $$;
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_service_orders_user_id "
        "ON core.service_orders(user_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS core.ix_service_orders_user_id")
    op.execute(
        "ALTER TABLE core.service_orders "
        "DROP CONSTRAINT IF EXISTS fk_service_orders_user_id"
    )
    op.execute("ALTER TABLE core.service_orders DROP COLUMN IF EXISTS user_id")

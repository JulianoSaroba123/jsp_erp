"""reconcile products/proposals/suppliers schema drift

Revision ID: 023_reconcile_products_proposals_suppliers
Revises: 022_service_order_enterprise_hardening
Create Date: 2026-05-28
"""

from alembic import op


revision = "023_reconcile_products_proposals_suppliers"
down_revision = "022_service_order_enterprise_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # products.user_id is required by ORM/service filters and may be missing in drifted DBs.
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS user_id UUID")
    op.execute(
        """
        WITH first_user AS (
            SELECT id
            FROM core.users
            ORDER BY created_at NULLS LAST, id
            LIMIT 1
        )
        UPDATE core.products p
        SET user_id = fu.id
        FROM first_user fu
        WHERE p.user_id IS NULL
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_products_user_id_users'
                  AND conrelid = 'core.products'::regclass
            ) THEN
                ALTER TABLE core.products
                    ADD CONSTRAINT fk_products_user_id_users
                    FOREIGN KEY (user_id)
                    REFERENCES core.users(id)
                    ON DELETE CASCADE;
            END IF;
        END $$;
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_user_id ON core.products(user_id)")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM core.products WHERE user_id IS NULL) THEN
                RAISE NOTICE 'core.products.user_id still has NULL values; keeping nullable to avoid migration failure';
            ELSE
                ALTER TABLE core.products ALTER COLUMN user_id SET NOT NULL;
            END IF;
        END $$;
        """
    )

    # proposals.parts_amount is read by Proposal ORM and may be absent in drifted DBs.
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS parts_amount NUMERIC(12,2) DEFAULT 0")
    op.execute("UPDATE core.proposals SET parts_amount = 0 WHERE parts_amount IS NULL")

    # suppliers.updated_at can be NULL in legacy rows and breaks SupplierOut validation.
    op.execute("ALTER TABLE core.suppliers ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute(
        """
        UPDATE core.suppliers
        SET updated_at = COALESCE(updated_at, created_at, now())
        WHERE updated_at IS NULL
        """
    )


def downgrade() -> None:
    # Reconcile migrations are intentionally non-destructive.
    pass

"""reconcile legacy column names for products and proposals

Revision ID: 025_reconcile_legacy_column_names
Revises: 024_reconcile_products_proposals_extended_fields
Create Date: 2026-05-28
"""

from alembic import op


revision = "025_reconcile_legacy_column_names"
down_revision = "024_reconcile_products_proposals_extended_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # products: legacy schemas used unit_price/stock_quantity/min_stock/is_active.
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS unit VARCHAR(20)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS sale_price NUMERIC(12,2) DEFAULT 0")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS stock_qty NUMERIC(12,3) DEFAULT 0")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS stock_min NUMERIC(12,3) DEFAULT 0")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS deleted_by UUID")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core' AND table_name = 'products' AND column_name = 'unit_price'
            ) THEN
                UPDATE core.products SET sale_price = COALESCE(sale_price, unit_price, 0);
            ELSE
                UPDATE core.products SET sale_price = COALESCE(sale_price, 0);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core' AND table_name = 'products' AND column_name = 'stock_quantity'
            ) THEN
                UPDATE core.products SET stock_qty = COALESCE(stock_qty, stock_quantity, 0);
            ELSE
                UPDATE core.products SET stock_qty = COALESCE(stock_qty, 0);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core' AND table_name = 'products' AND column_name = 'min_stock'
            ) THEN
                UPDATE core.products SET stock_min = COALESCE(stock_min, min_stock, 0);
            ELSE
                UPDATE core.products SET stock_min = COALESCE(stock_min, 0);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core' AND table_name = 'products' AND column_name = 'is_active'
            ) THEN
                UPDATE core.products SET active = COALESCE(active, is_active, true);
            ELSE
                UPDATE core.products SET active = COALESCE(active, true);
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
                WHERE conname = 'fk_products_deleted_by_users'
                  AND conrelid = 'core.products'::regclass
            ) THEN
                ALTER TABLE core.products
                    ADD CONSTRAINT fk_products_deleted_by_users
                    FOREIGN KEY (deleted_by)
                    REFERENCES core.users(id)
                    ON DELETE SET NULL;
            END IF;
        END $$;
        """
    )

    # proposals: legacy schemas used valid_until and lacked date workflow columns.
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS issue_date DATE DEFAULT CURRENT_DATE")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS validity_date DATE")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS approval_date DATE")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core' AND table_name = 'proposals' AND column_name = 'product_amount'
            ) THEN
                UPDATE core.proposals SET parts_amount = COALESCE(parts_amount, product_amount, 0);
            ELSE
                UPDATE core.proposals SET parts_amount = COALESCE(parts_amount, 0);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core' AND table_name = 'proposals' AND column_name = 'discount'
            ) THEN
                UPDATE core.proposals SET discount_amount = COALESCE(discount_amount, discount, 0);
            ELSE
                UPDATE core.proposals SET discount_amount = COALESCE(discount_amount, 0);
            END IF;
        END $$;
        """
    )
    op.execute("UPDATE core.proposals SET issue_date = COALESCE(issue_date, created_at::date, CURRENT_DATE)")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'core' AND table_name = 'proposals' AND column_name = 'valid_until'
            ) THEN
                UPDATE core.proposals SET validity_date = COALESCE(validity_date, valid_until);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Reconcile migration is non-destructive.
    pass

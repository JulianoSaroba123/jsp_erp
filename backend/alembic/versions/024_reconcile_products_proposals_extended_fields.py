"""reconcile products and proposals extended fields

Revision ID: 024_reconcile_products_proposals_extended_fields
Revises: 023_reconcile_products_proposals_suppliers
Create Date: 2026-05-28
"""

from alembic import op


revision = "024_reconcile_products_proposals_extended_fields"
down_revision = "023_reconcile_products_proposals_suppliers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Product extended columns from legacy/009 migration may be absent in drifted databases.
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS subcategoria VARCHAR(80)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS codigo_barras VARCHAR(50)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS marca VARCHAR(100)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS modelo VARCHAR(100)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS peso NUMERIC(10,3)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS dimensoes VARCHAR(100)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS markup NUMERIC(5,2)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS margem_lucro NUMERIC(5,2)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS estoque_maximo NUMERIC(12,3)")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS controla_estoque BOOLEAN DEFAULT true")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS fornecedor_id UUID")
    op.execute("ALTER TABLE core.products ADD COLUMN IF NOT EXISTS observacoes TEXT")

    # Proposal columns from 012/013 may be absent in stamped databases.
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12,2) DEFAULT 0")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS payment_condition VARCHAR(50)")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS delivery_days VARCHAR(50)")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS warranty_days VARCHAR(50)")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS approved_by VARCHAR(200)")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS share_token VARCHAR(64)")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS share_enabled BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS share_expires_at TIMESTAMP")
    op.execute("ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS share_created_at TIMESTAMP")

    op.execute("UPDATE core.proposals SET discount_amount = 0 WHERE discount_amount IS NULL")
    op.execute("UPDATE core.proposals SET share_enabled = false WHERE share_enabled IS NULL")

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_proposals_share_token "
        "ON core.proposals(share_token) WHERE share_token IS NOT NULL"
    )


def downgrade() -> None:
    # Reconcile migration is non-destructive.
    pass

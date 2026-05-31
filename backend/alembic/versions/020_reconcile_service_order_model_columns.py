"""reconcile service_order model columns

Revision ID: 020_reconcile_service_order_model_columns
Revises: 019_add_service_order_user_id
Create Date: 2026-05-17
"""

from alembic import op


revision = "020_reconcile_service_order_model_columns"
down_revision = "019_add_service_order_user_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS scheduled_date DATE")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS completed_date DATE")
    op.execute("ALTER TABLE core.service_orders ADD COLUMN IF NOT EXISTS deleted_by UUID")


def downgrade() -> None:
    op.drop_column("service_orders", "deleted_by", schema="core")
    op.drop_column("service_orders", "completed_date", schema="core")
    op.drop_column("service_orders", "scheduled_date", schema="core")

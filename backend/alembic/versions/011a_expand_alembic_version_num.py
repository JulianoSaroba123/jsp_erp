"""expand alembic version_num length

Revision ID: 011a_expand_alembic_version_num
Revises: 011_create_service_orders
Create Date: 2026-07-03 00:00:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "011a_expand_alembic_version_num"
down_revision = "011_create_service_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE core.alembic_version
        ALTER COLUMN version_num TYPE VARCHAR(100)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE core.alembic_version
        ALTER COLUMN version_num TYPE VARCHAR(32)
        """
    )

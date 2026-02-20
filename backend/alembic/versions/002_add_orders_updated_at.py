"""add orders updated_at column

Revision ID: 002_add_orders_updated_at
Revises: 001_baseline
Create Date: 2026-02-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_orders_updated_at'
down_revision = '001_baseline'
branch_labels = None
depends_on = None


def upgrade():
    """
    Adiciona coluna updated_at à tabela core.orders.
    
    - Inicia com NULL permitido
    - Define server_default=now() para novos registros
    - Popula registros existentes com created_at
    - Torna NOT NULL após população
    """
    # 1. Adicionar coluna com DEFAULT (para novos registros)
    op.add_column(
        'orders',
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            nullable=True,  # Temporariamente NULL
            server_default=sa.text('now()')
        ),
        schema='core'
    )
    
    # 2. Preencher valores existentes com created_at
    op.execute("""
        UPDATE core.orders
        SET updated_at = created_at
        WHERE updated_at IS NULL
    """)
    
    # 3. Tornar coluna NOT NULL após população
    op.alter_column(
        'orders',
        'updated_at',
        nullable=False,
        schema='core'
    )


def downgrade():
    """
    Remove coluna updated_at da tabela core.orders.
    """
    op.drop_column('orders', 'updated_at', schema='core')

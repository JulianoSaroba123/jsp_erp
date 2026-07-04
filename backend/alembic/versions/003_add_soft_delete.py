"""Add soft delete columns

Revision ID: 003
Revises: 002_audit_logs, 002_add_orders_updated_at (MERGE)
Create Date: 2026-02-18 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
# MERGE: Esta migration une dois branches paralelos
down_revision = ('002_audit_logs', '002_add_orders_updated_at')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona colunas de soft delete (deleted_at, deleted_by) 
    nas tabelas orders e financial_entries.
    """
    
    # Adicionar colunas em core.orders
    op.add_column(
        'orders',
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        schema='core'
    )
    op.add_column(
        'orders',
        sa.Column('deleted_by', sa.UUID(), nullable=True),
        schema='core'
    )
    
    # FK para deleted_by -> users
    op.create_foreign_key(
        'fk_orders_deleted_by_users',
        'orders', 'users',
        ['deleted_by'], ['id'],
        source_schema='core',
        referent_schema='core',
        ondelete='SET NULL'
    )
    
    # Índice para performance em queries com soft delete
    op.create_index(
        'ix_orders_deleted_at',
        'orders',
        ['deleted_at'],
        schema='core'
    )
    
    # Adicionar colunas em core.financial_entries
    op.add_column(
        'financial_entries',
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        schema='core'
    )
    op.add_column(
        'financial_entries',
        sa.Column('deleted_by', sa.UUID(), nullable=True),
        schema='core'
    )
    
    # FK para deleted_by -> users
    op.create_foreign_key(
        'fk_financial_entries_deleted_by_users',
        'financial_entries', 'users',
        ['deleted_by'], ['id'],
        source_schema='core',
        referent_schema='core',
        ondelete='SET NULL'
    )
    
    # Índice para performance
    op.create_index(
        'ix_financial_entries_deleted_at',
        'financial_entries',
        ['deleted_at'],
        schema='core'
    )
    
    # Comentários (1 op.execute por statement — psycopg v3 não aceita múltiplos)
    op.execute("COMMENT ON COLUMN core.orders.deleted_at IS 'Timestamp de quando o registro foi soft-deleted (NULL = ativo)'")
    op.execute("COMMENT ON COLUMN core.orders.deleted_by IS 'ID do usuário que deletou o registro'")
    op.execute("COMMENT ON COLUMN core.financial_entries.deleted_at IS 'Timestamp de quando o registro foi soft-deleted (NULL = ativo)'")
    op.execute("COMMENT ON COLUMN core.financial_entries.deleted_by IS 'ID do usuário que deletou o registro'")


def downgrade() -> None:
    """
    Remove colunas de soft delete das tabelas orders e financial_entries.
    """
    
    # Remover de financial_entries
    op.drop_index('ix_financial_entries_deleted_at', table_name='financial_entries', schema='core')
    op.drop_constraint('fk_financial_entries_deleted_by_users', 'financial_entries', schema='core', type_='foreignkey')
    op.drop_column('financial_entries', 'deleted_by', schema='core')
    op.drop_column('financial_entries', 'deleted_at', schema='core')
    
    # Remover de orders
    op.drop_index('ix_orders_deleted_at', table_name='orders', schema='core')
    op.drop_constraint('fk_orders_deleted_by_users', 'orders', schema='core', type_='foreignkey')
    op.drop_column('orders', 'deleted_by', schema='core')
    op.drop_column('orders', 'deleted_at', schema='core')

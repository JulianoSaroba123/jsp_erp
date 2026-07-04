"""Add products table

Revision ID: 008_add_products
Revises: 007_enhance_customers
Create Date: 2026-03-04 00:00:00.000000

ETAPA 6 - Products Module
==========================

Cria tabela core.products com:
- Isolamento por user_id (admin vê tudo, usuários veem só os seus)
- Soft delete (deleted_at)
- Check constraints para valores numéricos >= 0
- Índices para performance
- FK para core.users

Campos MVP:
- id, user_id, code, name, category, unit, description
- cost_price, sale_price, stock_qty, stock_min
- active, created_at, updated_at, deleted_at, deleted_by

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '008_add_products'
down_revision = '007_enhance_customers'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cria tabela core.products.
    """
    
    # Usar connection para DDL com CheckConstraint
    connection = op.get_bind()
    
    # Criar tabela products
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=80), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cost_price', sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('sale_price', sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('stock_qty', sa.Numeric(precision=12, scale=3), nullable=False, server_default=sa.text('0')),
        sa.Column('stock_min', sa.Numeric(precision=12, scale=3), nullable=False, server_default=sa.text('0')),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Primary Key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deleted_by'], ['core.users.id'], ondelete='SET NULL'),
        
        # Check Constraints
        sa.CheckConstraint('cost_price >= 0', name='check_product_cost_price_positive'),
        sa.CheckConstraint('sale_price >= 0', name='check_product_sale_price_positive'),
        sa.CheckConstraint('stock_qty >= 0', name='check_product_stock_qty_positive'),
        sa.CheckConstraint('stock_min >= 0', name='check_product_stock_min_positive'),
        
        schema='core'
    )
    
    # Criar índices para performance
    op.create_index('idx_products_user_id', 'products', ['user_id'], unique=False, schema='core')
    op.create_index('idx_products_name', 'products', ['name'], unique=False, schema='core')
    op.create_index('idx_products_code', 'products', ['code'], unique=False, schema='core')
    op.create_index('idx_products_category', 'products', ['category'], unique=False, schema='core')
    op.create_index('idx_products_active', 'products', ['active'], unique=False, schema='core')
    op.create_index('idx_products_deleted_at', 'products', ['deleted_at'], unique=False, schema='core')
    
    # Índice composto para queries user_id + filtros
    op.create_index('idx_products_user_category', 'products', ['user_id', 'category'], unique=False, schema='core')
    op.create_index('idx_products_user_active', 'products', ['user_id', 'active'], unique=False, schema='core')


def downgrade():
    """
    Remove tabela core.products.
    """
    
    # Drop índices primeiro
    op.drop_index('idx_products_user_active', table_name='products', schema='core')
    op.drop_index('idx_products_user_category', table_name='products', schema='core')
    op.drop_index('idx_products_deleted_at', table_name='products', schema='core')
    op.drop_index('idx_products_active', table_name='products', schema='core')
    op.drop_index('idx_products_category', table_name='products', schema='core')
    op.drop_index('idx_products_code', table_name='products', schema='core')
    op.drop_index('idx_products_name', table_name='products', schema='core')
    op.drop_index('idx_products_user_id', table_name='products', schema='core')
    
    # Drop tabela
    op.drop_table('products', schema='core')

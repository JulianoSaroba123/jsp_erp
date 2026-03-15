"""Extend products table with advanced fields

Revision ID: 009_extend_products
Revises: 008_add_products
Create Date: 2026-03-05 00:00:00.000000

ETAPA 6 - Products Module - Extended Fields
============================================

Adiciona campos avançados do sistema legado:

Identificação Estendida:
- codigo_barras (código de barras único)
- marca, modelo (identificação do fabricante)
- subcategoria (hierarquia de categorização)

Características Físicas:
- peso (kg/g para logística)
- dimensoes (LxAxP para embalagem)

Gestão de Preços:
- markup (% sobre custo)
- margem_lucro (% de lucro calculado)

Gestão de Estoque:
- estoque_maximo (limite superior)
- controla_estoque (ativar/desativar controle)

Relacionamentos e Observações:
- fornecedor_id (FK para fornecedores - futuro)
- observacoes (notas gerais)

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '009_extend_products'
down_revision = '008_add_products'
branch_labels = None
depends_on = None


def upgrade():
    """
    Adiciona campos avançados à tabela core.products.
    """
    
    # Identificação Estendida
    op.add_column('products', sa.Column('codigo_barras', sa.String(length=50), nullable=True), schema='core')
    op.add_column('products', sa.Column('marca', sa.String(length=100), nullable=True), schema='core')
    op.add_column('products', sa.Column('modelo', sa.String(length=100), nullable=True), schema='core')
    op.add_column('products', sa.Column('subcategoria', sa.String(length=80), nullable=True), schema='core')
    
    # Características Físicas
    op.add_column('products', sa.Column('peso', sa.Numeric(precision=10, scale=3), nullable=True), schema='core')
    op.add_column('products', sa.Column('dimensoes', sa.String(length=100), nullable=True), schema='core')
    
    # Gestão de Preços
    op.add_column('products', sa.Column('markup', sa.Numeric(precision=5, scale=2), nullable=True), schema='core')
    op.add_column('products', sa.Column('margem_lucro', sa.Numeric(precision=5, scale=2), nullable=True), schema='core')
    
    # Gestão de Estoque
    op.add_column('products', sa.Column('estoque_maximo', sa.Numeric(precision=12, scale=3), nullable=True), schema='core')
    op.add_column('products', sa.Column('controla_estoque', sa.Boolean(), nullable=False, server_default=sa.text('true')), schema='core')
    
    # Relacionamentos
    op.add_column('products', sa.Column('fornecedor_id', postgresql.UUID(as_uuid=True), nullable=True), schema='core')
    
    # Observações
    op.add_column('products', sa.Column('observacoes', sa.Text(), nullable=True), schema='core')
    
    # Criar índice único para codigo_barras (apenas valores não-nulos)
    op.execute("""
        CREATE UNIQUE INDEX idx_products_codigo_barras_unique 
        ON core.products (codigo_barras) 
        WHERE codigo_barras IS NOT NULL AND deleted_at IS NULL
    """)
    
    # Índices para melhor performance em buscas
    op.create_index('idx_products_marca', 'products', ['marca'], unique=False, schema='core')
    op.create_index('idx_products_subcategoria', 'products', ['subcategoria'], unique=False, schema='core')
    
    # Índice composto para user_id + subcategoria (queries filtradas)
    op.create_index('idx_products_user_subcategoria', 'products', ['user_id', 'subcategoria'], unique=False, schema='core')
    
    # Check Constraints para validar valores
    op.create_check_constraint(
        'check_product_peso_positive',
        'products',
        'peso IS NULL OR peso >= 0',
        schema='core'
    )
    
    op.create_check_constraint(
        'check_product_markup_valid',
        'products',
        'markup IS NULL OR (markup >= 0 AND markup <= 1000)',
        schema='core'
    )
    
    op.create_check_constraint(
        'check_product_margem_lucro_valid',
        'products',
        'margem_lucro IS NULL OR (margem_lucro >= -100 AND margem_lucro <= 1000)',
        schema='core'
    )
    
    op.create_check_constraint(
        'check_product_estoque_maximo_positive',
        'products',
        'estoque_maximo IS NULL OR estoque_maximo >= 0',
        schema='core'
    )


def downgrade():
    """
    Remove campos avançados da tabela core.products.
    """
    
    # Drop check constraints
    op.drop_constraint('check_product_estoque_maximo_positive', 'products', schema='core')
    op.drop_constraint('check_product_margem_lucro_valid', 'products', schema='core')
    op.drop_constraint('check_product_markup_valid', 'products', schema='core')
    op.drop_constraint('check_product_peso_positive', 'products', schema='core')
    
    # Drop índices
    op.drop_index('idx_products_user_subcategoria', table_name='products', schema='core')
    op.drop_index('idx_products_subcategoria', table_name='products', schema='core')
    op.drop_index('idx_products_marca', table_name='products', schema='core')
    op.execute('DROP INDEX IF EXISTS core.idx_products_codigo_barras_unique')
    
    # Drop colunas
    op.drop_column('products', 'observacoes', schema='core')
    op.drop_column('products', 'fornecedor_id', schema='core')
    op.drop_column('products', 'controla_estoque', schema='core')
    op.drop_column('products', 'estoque_maximo', schema='core')
    op.drop_column('products', 'margem_lucro', schema='core')
    op.drop_column('products', 'markup', schema='core')
    op.drop_column('products', 'dimensoes', schema='core')
    op.drop_column('products', 'peso', schema='core')
    op.drop_column('products', 'subcategoria', schema='core')
    op.drop_column('products', 'modelo', schema='core')
    op.drop_column('products', 'marca', schema='core')
    op.drop_column('products', 'codigo_barras', schema='core')

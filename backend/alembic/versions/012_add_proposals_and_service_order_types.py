"""012_add_proposals_and_service_order_types

Create proposals tables and add tipo_ordem fields to service_orders

Revision ID: 012_add_proposals_and_service_order_types
Revises: 011a_expand_alembic_version_num
Create Date: 2026-03-11 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '012_add_proposals_and_service_order_types'
down_revision = '011a_expand_alembic_version_num'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Criação de tabelas de propostas e adição de campos de tipo_ordem no service_orders
    """
    
    # ========== TABELA DE PROPOSTAS ==========
    op.create_table(
        'proposals',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_contact', sa.String(length=200), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('service_amount', sa.Numeric(precision=12, scale=2), server_default=sa.text('0'), nullable=True),
        sa.Column('parts_amount', sa.Numeric(precision=12, scale=2), server_default=sa.text('0'), nullable=True),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), server_default=sa.text('0'), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), server_default=sa.text('0'), nullable=False),
        sa.Column('issue_date', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.Column('validity_date', sa.Date(), nullable=True),
        sa.Column('approval_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'rascunho'"), nullable=False),
        sa.Column('payment_condition', sa.String(length=50), nullable=True),
        sa.Column('delivery_days', sa.String(length=50), nullable=True),
        sa.Column('warranty_days', sa.String(length=50), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deleted_by'], ['core.users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('number'),
        schema='core'
    )
    
    # Índices para proposals
    op.create_index(op.f('ix_core_proposals_number'), 'proposals', ['number'], unique=True, schema='core')
    op.create_index(op.f('ix_core_proposals_customer_id'), 'proposals', ['customer_id'], unique=False, schema='core')
    op.create_index(op.f('ix_core_proposals_status'), 'proposals', ['status'], unique=False, schema='core')
    op.create_index(op.f('ix_core_proposals_user_id'), 'proposals', ['user_id'], unique=False, schema='core')
    op.create_index(op.f('ix_core_proposals_deleted_at'), 'proposals', ['deleted_at'], unique=False, schema='core')
    
    # ========== ITENS DE PROPOSTA ==========
    op.create_table(
        'proposal_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('proposal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('service_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['proposal_id'], ['core.proposals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='core'
    )
    
    op.create_index(op.f('ix_core_proposal_items_proposal_id'), 'proposal_items', ['proposal_id'], unique=False, schema='core')
    
    # ========== PRODUTOS DE PROPOSTA ==========
    op.create_table(
        'proposal_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('proposal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['proposal_id'], ['core.proposals.id'], ondelete='CASCADE'),
        # FK para products será criada separadamente
        sa.PrimaryKeyConstraint('id'),
        schema='core'
    )
    
    op.create_index(op.f('ix_core_proposal_products_proposal_id'), 'proposal_products', ['proposal_id'], unique=False, schema='core')
    
    # Criar FK para products se a tabela existir
    # Conexão para verificar existência
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'core' AND tablename = 'products')"))
    products_exists = result.scalar()
    
    if products_exists:
        op.create_foreign_key(
            'fk_proposal_products_product_id',
            'proposal_products', 'products',
            ['product_id'], ['id'],
            source_schema='core', referent_schema='core',
            ondelete='RESTRICT'
        )
    
    # ========== ADICIONAR CAMPOS AO SERVICE_ORDERS ==========
    
    # 1. tipo_ordem: indica se é OS de atendimento (emergencial/cobrado) ou projeto (acompanhamento)
    op.add_column('service_orders', sa.Column('tipo_ordem', sa.String(length=20), nullable=True), schema='core')
    
    # 2. exibir_valores: controla se valores aparecem no relatório/PDF
    op.add_column('service_orders', sa.Column('exibir_valores', sa.Boolean(), nullable=True), schema='core')
    
    # 3. proposta_id: vincula OS com proposta aprovada
    op.add_column('service_orders', sa.Column('proposta_id', postgresql.UUID(as_uuid=True), nullable=True), schema='core')
    
    # 4. percentual_concluido: andamento do projeto (0-100)
    op.add_column('service_orders', sa.Column('percentual_concluido', sa.Integer(), nullable=True), schema='core')
    
    # 5. etapa_atual: fase atual do projeto
    op.add_column('service_orders', sa.Column('etapa_atual', sa.String(length=200), nullable=True), schema='core')
    
    # ========== PREENCHER DEFAULTS PARA DADOS EXISTENTES ==========
    # IMPORTANTE: Migração segura para OS existentes
    # Estratégia: OS sem proposta_id = "atendimento" (cenário mais comum)
    #             OS com proposta_id (quando implementado) = "projeto"
    
    op.execute("""
        UPDATE core.service_orders 
        SET 
            tipo_ordem = 'atendimento',
            exibir_valores = TRUE,
            percentual_concluido = 0
        WHERE tipo_ordem IS NULL;
    """)
    
    # ========== TORNAR COLUNAS NOT NULL APÓS PREENCHER ==========
    op.alter_column('service_orders', 'tipo_ordem', nullable=False, schema='core')
    op.alter_column('service_orders', 'exibir_valores', nullable=False, schema='core')
    op.alter_column('service_orders', 'percentual_concluido', nullable=False, server_default=sa.text('0'), schema='core')
    
    # ========== CRIAR FK e ÍNDICES ==========
    op.create_foreign_key(
        'fk_service_orders_proposta_id',
        'service_orders', 'proposals',
        ['proposta_id'], ['id'],
        source_schema='core', referent_schema='core',
        ondelete='SET NULL'
    )
    
    op.create_index(op.f('ix_core_service_orders_tipo_ordem'), 'service_orders', ['tipo_ordem'], unique=False, schema='core')
    op.create_index(op.f('ix_core_service_orders_proposta_id'), 'service_orders', ['proposta_id'], unique=False, schema='core')
    
    print("✅ Migration 012: Proposals e tipos de OS criados com sucesso!")


def downgrade() -> None:
    """
    Reverter criação de propostas e campos de tipo_ordem
    """
    
    # Remover FK e índices de service_orders
    op.drop_index(op.f('ix_core_service_orders_proposta_id'), table_name='service_orders', schema='core')
    op.drop_index(op.f('ix_core_service_orders_tipo_ordem'), table_name='service_orders', schema='core')
    op.drop_constraint('fk_service_orders_proposta_id', 'service_orders', type_='foreignkey', schema='core')
    
    # Remover colunas de service_orders
    op.drop_column('service_orders', 'etapa_atual', schema='core')
    op.drop_column('service_orders', 'percentual_concluido', schema='core')
    op.drop_column('service_orders', 'proposta_id', schema='core')
    op.drop_column('service_orders', 'exibir_valores', schema='core')
    op.drop_column('service_orders', 'tipo_ordem', schema='core')
    
    # Remover tabelas de propostas (ordem inversa da criação)
    op.drop_index(op.f('ix_core_proposal_products_proposal_id'), table_name='proposal_products', schema='core')
    op.drop_table('proposal_products', schema='core')
    
    op.drop_index(op.f('ix_core_proposal_items_proposal_id'), table_name='proposal_items', schema='core')
    op.drop_table('proposal_items', schema='core')
    
    op.drop_index(op.f('ix_core_proposals_deleted_at'), table_name='proposals', schema='core')
    op.drop_index(op.f('ix_core_proposals_user_id'), table_name='proposals', schema='core')
    op.drop_index(op.f('ix_core_proposals_status'), table_name='proposals', schema='core')
    op.drop_index(op.f('ix_core_proposals_customer_id'), table_name='proposals', schema='core')
    op.drop_index(op.f('ix_core_proposals_number'), table_name='proposals', schema='core')
    op.drop_table('proposals', schema='core')
    
    print("⬇️ Migration 012: Rollback completo!")

"""014 - Enhance financial entries with professional fields

Revision ID: 014_enhance_financial
Revises: 6323d5edc547
Create Date: 2026-04-05 11:00:00

Description:
    Adiciona campos profissionais ao sistema financeiro:
    - Categorização (categoria, subcategoria)
    - Controle de datas (due_date, payment_date)
    - Documentação (document_number, document_type)
    - Relacionamentos (customer_id, supplier_id, service_order_id)
    - Valores calculados (original_amount, interest, discount, penalty)
    - Parcelamento (installment_info)
    - Recorrência (is_recurring, recurrence_frequency)
    - Rastreabilidade (origin)
    - Método de pagamento (payment_method)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_enhance_financial'
down_revision = '6323d5edc547'
branch_labels = None
depends_on = None


def upgrade():
    """Adiciona campos profissionais à tabela financial_entries."""
    
    # Categorização
    op.add_column('financial_entries', sa.Column('category', sa.String(100), nullable=True), schema='core')
    op.add_column('financial_entries', sa.Column('subcategory', sa.String(100), nullable=True), schema='core')
    
    # Controle de datas
    op.add_column('financial_entries', sa.Column('due_date', sa.TIMESTAMP(timezone=True), nullable=True), schema='core')
    op.add_column('financial_entries', sa.Column('payment_date', sa.TIMESTAMP(timezone=True), nullable=True), schema='core')
    
    # Documentação
    op.add_column('financial_entries', sa.Column('document_number', sa.String(50), nullable=True), schema='core')
    op.add_column('financial_entries', sa.Column('document_type', sa.String(30), nullable=True), schema='core')
    
    # Método de pagamento
    op.add_column('financial_entries', sa.Column('payment_method', sa.String(50), nullable=True), schema='core')
    
    # Observações adicionais
    op.add_column('financial_entries', sa.Column('notes', sa.Text(), nullable=True), schema='core')
    
    # Relacionamentos FK
    op.add_column('financial_entries', sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True), schema='core')
    op.add_column('financial_entries', sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True), schema='core')
    op.add_column('financial_entries', sa.Column('service_order_id', postgresql.UUID(as_uuid=True), nullable=True), schema='core')
    
    # Valores calculados
    op.add_column('financial_entries', sa.Column('original_amount', sa.Numeric(12, 2), nullable=True), schema='core')
    op.add_column('financial_entries', sa.Column('interest', sa.Numeric(12, 2), server_default='0', nullable=False), schema='core')
    op.add_column('financial_entries', sa.Column('discount', sa.Numeric(12, 2), server_default='0', nullable=False), schema='core')
    op.add_column('financial_entries', sa.Column('penalty', sa.Numeric(12, 2), server_default='0', nullable=False), schema='core')
    
    # Parcelamento
    op.add_column('financial_entries', sa.Column('installment_info', sa.String(20), nullable=True), schema='core')
    
    # Recorrência
    op.add_column('financial_entries', sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False), schema='core')
    op.add_column('financial_entries', sa.Column('recurrence_frequency', sa.String(20), nullable=True), schema='core')
    
    # Origem/Rastreabilidade
    op.add_column('financial_entries', sa.Column('origin', sa.String(50), server_default='MANUAL', nullable=False), schema='core')
    
    # Criar FKs
    op.create_foreign_key(
        'fk_financial_entries_customer',
        'financial_entries', 'customers',
        ['customer_id'], ['id'],
        source_schema='core', referent_schema='core',
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_financial_entries_supplier',
        'financial_entries', 'suppliers',
        ['supplier_id'], ['id'],
        source_schema='core', referent_schema='core',
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_financial_entries_service_order',
        'financial_entries', 'service_orders',
        ['service_order_id'], ['id'],
        source_schema='core', referent_schema='core',
        ondelete='SET NULL'
    )
    
    # Criar índices para performance
    op.create_index('ix_financial_entries_category', 'financial_entries', ['category'], schema='core')
    op.create_index('ix_financial_entries_due_date', 'financial_entries', ['due_date'], schema='core')
    op.create_index('ix_financial_entries_payment_date', 'financial_entries', ['payment_date'], schema='core')
    op.create_index('ix_financial_entries_customer_id', 'financial_entries', ['customer_id'], schema='core')
    op.create_index('ix_financial_entries_supplier_id', 'financial_entries', ['supplier_id'], schema='core')
    op.create_index('ix_financial_entries_service_order_id', 'financial_entries', ['service_order_id'], schema='core')


def downgrade():
    """Remove campos profissionais da tabela financial_entries."""
    
    # Remover índices
    op.drop_index('ix_financial_entries_service_order_id', table_name='financial_entries', schema='core')
    op.drop_index('ix_financial_entries_supplier_id', table_name='financial_entries', schema='core')
    op.drop_index('ix_financial_entries_customer_id', table_name='financial_entries', schema='core')
    op.drop_index('ix_financial_entries_payment_date', table_name='financial_entries', schema='core')
    op.drop_index('ix_financial_entries_due_date', table_name='financial_entries', schema='core')
    op.drop_index('ix_financial_entries_category', table_name='financial_entries', schema='core')
    
    # Remover FKs
    op.drop_constraint('fk_financial_entries_service_order', 'financial_entries', schema='core', type_='foreignkey')
    op.drop_constraint('fk_financial_entries_supplier', 'financial_entries', schema='core', type_='foreignkey')
    op.drop_constraint('fk_financial_entries_customer', 'financial_entries', schema='core', type_='foreignkey')
    
    # Remover colunas
    op.drop_column('financial_entries', 'origin', schema='core')
    op.drop_column('financial_entries', 'recurrence_frequency', schema='core')
    op.drop_column('financial_entries', 'is_recurring', schema='core')
    op.drop_column('financial_entries', 'installment_info', schema='core')
    op.drop_column('financial_entries', 'penalty', schema='core')
    op.drop_column('financial_entries', 'discount', schema='core')
    op.drop_column('financial_entries', 'interest', schema='core')
    op.drop_column('financial_entries', 'original_amount', schema='core')
    op.drop_column('financial_entries', 'service_order_id', schema='core')
    op.drop_column('financial_entries', 'supplier_id', schema='core')
    op.drop_column('financial_entries', 'customer_id', schema='core')
    op.drop_column('financial_entries', 'notes', schema='core')
    op.drop_column('financial_entries', 'payment_method', schema='core')
    op.drop_column('financial_entries', 'document_type', schema='core')
    op.drop_column('financial_entries', 'document_number', schema='core')
    op.drop_column('financial_entries', 'payment_date', schema='core')
    op.drop_column('financial_entries', 'due_date', schema='core')
    op.drop_column('financial_entries', 'subcategory', schema='core')
    op.drop_column('financial_entries', 'category', schema='core')

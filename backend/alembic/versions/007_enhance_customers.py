"""enhance_customers_table

Revision ID: 007_enhance_customers
Revises: 006_add_customers
Create Date: 2026-03-02 15:00:00.000000

ETAPA 6: MELHORIAS NO MÓDULO DE CLIENTES
=========================================

Esta migration adiciona novos campos à tabela customers para torná-la mais completa:
- person_type (PF/PJ)
- trade_name (nome fantasia)
- state_registration (inscrição estadual)
- phone2 (telefone alternativo)
- address_complement (complemento)
- notes (observações)
- status (ativo/inativo)

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_enhance_customers'
down_revision = '006_add_customers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona novos campos à tabela core.customers
    """
    
    # Adicionar novos campos
    op.add_column('customers', sa.Column('person_type', sa.String(length=2), nullable=True, server_default='PF'), schema='core')
    op.add_column('customers', sa.Column('trade_name', sa.String(length=120), nullable=True), schema='core')
    op.add_column('customers', sa.Column('state_registration', sa.String(length=20), nullable=True), schema='core')
    op.add_column('customers', sa.Column('phone2', sa.String(length=15), nullable=True), schema='core')
    op.add_column('customers', sa.Column('address_complement', sa.String(length=100), nullable=True), schema='core')
    op.add_column('customers', sa.Column('notes', sa.Text(), nullable=True), schema='core')
    op.add_column('customers', sa.Column('status', sa.String(length=10), nullable=False, server_default='active'), schema='core')


def downgrade() -> None:
    """
    Remove os novos campos da tabela core.customers
    """
    op.drop_column('customers', 'status', schema='core')
    op.drop_column('customers', 'notes', schema='core')
    op.drop_column('customers', 'address_complement', schema='core')
    op.drop_column('customers', 'phone2', schema='core')
    op.drop_column('customers', 'state_registration', schema='core')
    op.drop_column('customers', 'trade_name', schema='core')
    op.drop_column('customers', 'person_type', schema='core')

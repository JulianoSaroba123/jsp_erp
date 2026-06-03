"""add_customers_table

Revision ID: 006_add_customers
Revises: 005_rbac_idempotent
Create Date: 2026-03-02 00:00:00.000000

ETAPA 6: MÓDULO DE CLIENTES
============================

Esta migration cria a tabela core.customers para o módulo de clientes.

Estrutura:
- Tabela core.customers com todos os campos necessários
- Soft delete (deleted_at)
- Índices para performance (name, cpf_cnpj, deleted_at)
- Constraint para CPF/CNPJ único (quando não deletado)

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_customers'
down_revision = '005_rbac_idempotent'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Cria tabela core.customers
    """
    
    # Criar tabela customers
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('cpf_cnpj', sa.String(length=14), nullable=True),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('phone', sa.String(length=15), nullable=True),
        sa.Column('cep', sa.String(length=8), nullable=True),
        sa.Column('street', sa.String(length=200), nullable=True),
        sa.Column('number', sa.String(length=20), nullable=True),
        sa.Column('neighborhood', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='core'
    )
    
    # Índices para performance
    op.create_index('ix_core_customers_name', 'customers', ['name'], schema='core')
    op.create_index('ix_core_customers_cpf_cnpj', 'customers', ['cpf_cnpj'], schema='core')
    op.create_index('ix_core_customers_deleted_at', 'customers', ['deleted_at'], schema='core')
    
    # Constraint: CPF/CNPJ único quando não deletado
    op.execute("""
        CREATE UNIQUE INDEX ix_core_customers_cpf_cnpj_unique 
        ON core.customers (cpf_cnpj) 
        WHERE deleted_at IS NULL AND cpf_cnpj IS NOT NULL
    """)


def downgrade() -> None:
    """
    Remove tabela core.customers
    """
    op.drop_index('ix_core_customers_cpf_cnpj_unique', table_name='customers', schema='core')
    op.drop_index('ix_core_customers_deleted_at', table_name='customers', schema='core')
    op.drop_index('ix_core_customers_cpf_cnpj', table_name='customers', schema='core')
    op.drop_index('ix_core_customers_name', table_name='customers', schema='core')
    op.drop_table('customers', schema='core')

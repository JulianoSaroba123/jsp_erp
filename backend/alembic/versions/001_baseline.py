"""baseline_schema_core_users_orders_financial

Revision ID: 001_baseline
Revises: 
Create Date: 2026-02-16 00:00:00.000000

BASELINE MIGRATION - ETAPA 3B
==============================

Esta migration cria o schema inicial do projeto:
- Schema "core"
- Tabela core.users (autenticação e usuários)
- Tabela core.orders (pedidos)
- Tabela core.financial_entries (lançamentos financeiros)
- Constraints, checks, FKs, índices de performance

IMPORTANTE:
-----------
Se o banco JÁ POSSUI estas tabelas (via scripts SQL anteriores):
    alembic stamp 001_baseline
    
Se o banco está vazio:
    alembic upgrade head

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Cria schema core + tabelas + constraints + índices.
    """
    
    # =====================================
    # 0. Criar extensão pgcrypto (para gen_random_uuid)
    # =====================================
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    
    # =====================================
    # 1. Criar schema "core"
    # =====================================
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    
    
    # =====================================
    # 2. Tabela core.users
    # =====================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='users_pkey'),
        sa.UniqueConstraint('email', name='users_email_key'),
        sa.CheckConstraint("role IN ('admin', 'user', 'technician', 'finance')", name='check_user_role'),
        schema='core'
    )
    
    # Comentários (1 op.execute por statement — psycopg v3 não aceita múltiplos)
    op.execute("COMMENT ON TABLE core.users IS 'Tabela de usuários do sistema com autenticação'")
    op.execute("COMMENT ON COLUMN core.users.password_hash IS 'Hash bcrypt da senha (nunca expor em APIs)'")
    op.execute("COMMENT ON COLUMN core.users.role IS 'Papel do usuário: admin, user, technician, finance'")
    op.execute("COMMENT ON COLUMN core.users.is_active IS 'Flag de ativação (soft delete)'")
    
    
    # =====================================
    # 3. Tabela core.orders
    # =====================================
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('total', sa.Numeric(precision=12, scale=2), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='orders_pkey'),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], name='orders_user_id_fkey', ondelete='CASCADE'),
        schema='core'
    )
    
    # Índice para user_id (multi-tenant queries)
    op.create_index('ix_core_orders_user_id', 'orders', ['user_id'], schema='core')
    
    # Comentários (1 op.execute por statement — psycopg v3 não aceita múltiplos)
    op.execute("COMMENT ON TABLE core.orders IS 'Tabela de pedidos/ordens do sistema'")
    op.execute("COMMENT ON COLUMN core.orders.user_id IS 'FK para usuário dono do pedido (multi-tenant)'")
    op.execute("COMMENT ON COLUMN core.orders.total IS 'Valor total do pedido'")
    
    
    # =====================================
    # 4. Tabela core.financial_entries
    # =====================================
    op.create_table(
        'financial_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.VARCHAR(length=20), nullable=False),
        sa.Column('status', sa.VARCHAR(length=20), server_default=sa.text("'pending'"), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('occurred_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name='financial_entries_pkey'),
        sa.ForeignKeyConstraint(['order_id'], ['core.orders.id'], name='financial_entries_order_id_fkey', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], name='financial_entries_user_id_fkey', ondelete='CASCADE'),
        sa.UniqueConstraint('order_id', name='unique_order_entry'),
        sa.CheckConstraint("kind IN ('revenue', 'expense')", name='check_financial_kind'),
        sa.CheckConstraint("status IN ('pending', 'paid', 'canceled')", name='check_financial_status'),
        sa.CheckConstraint('amount >= 0', name='check_financial_amount_positive'),
        schema='core'
    )
    
    # Índices de performance (críticos para relatórios e queries multi-tenant)
    # Índice composto com DESC requer op.execute direto
    op.execute("""
        CREATE INDEX idx_financial_entries_user_occurred
        ON core.financial_entries (user_id, occurred_at DESC)
    """)
    op.create_index('idx_financial_entries_status', 'financial_entries', ['status'], schema='core')
    op.create_index('idx_financial_entries_kind', 'financial_entries', ['kind'], schema='core')
    
    # Partial index para lançamentos vinculados a pedidos
    op.execute("""
        CREATE INDEX idx_financial_entries_order 
        ON core.financial_entries(order_id) 
        WHERE order_id IS NOT NULL
    """)
    
    # Comentários (1 op.execute por statement — psycopg v3 não aceita múltiplos)
    op.execute("COMMENT ON TABLE core.financial_entries IS 'Lançamentos financeiros (receitas/despesas) com integração automática de pedidos'")
    op.execute("COMMENT ON COLUMN core.financial_entries.order_id IS 'FK para order (NULL se lançamento manual)'")
    op.execute("COMMENT ON COLUMN core.financial_entries.kind IS 'Tipo: revenue (receita) ou expense (despesa)'")
    op.execute("COMMENT ON COLUMN core.financial_entries.status IS 'Status: pending, paid, canceled'")
    op.execute("COMMENT ON COLUMN core.financial_entries.occurred_at IS 'Data de ocorrência do lançamento'")
    op.execute("COMMENT ON CONSTRAINT unique_order_entry ON core.financial_entries IS 'Garante um único lançamento automático por pedido'")
    op.execute("COMMENT ON INDEX core.idx_financial_entries_user_occurred IS 'Otimiza consultas multi-tenant ordenadas por data'")
    op.execute("COMMENT ON INDEX core.idx_financial_entries_status IS 'Otimiza filtros por status (pending, paid, canceled)'")
    op.execute("COMMENT ON INDEX core.idx_financial_entries_order IS 'Partial index para lançamentos vinculados a pedidos'")
    op.execute("COMMENT ON INDEX core.idx_financial_entries_kind IS 'Otimiza filtros por tipo (revenue/expense)'")


def downgrade() -> None:
    """
    Remove schema core e todas as tabelas.
    
    ATENÇÃO: Esta operação é DESTRUTIVA e remove TODOS os dados.
    Use com extremo cuidado.
    """
    
    # Drop tabelas na ordem reversa (respeitando FKs)
    op.drop_table('financial_entries', schema='core')
    op.drop_table('orders', schema='core')
    op.drop_table('users', schema='core')
    
    # Drop schema core
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")

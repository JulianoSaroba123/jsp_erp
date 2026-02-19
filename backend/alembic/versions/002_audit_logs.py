"""add audit_logs table

Revision ID: 002_audit_logs
Revises: 001_baseline
Create Date: 2026-02-18 00:00:00.000000

ETAPA 6 - AUDIT LOG
===================

Esta migration adiciona a tabela audit_logs para rastreabilidade completa:
- Registra todas operações CREATE, UPDATE, DELETE
- Armazena estado antes/depois (JSON)
- Vincula com request_id do middleware
- Índices otimizados para consultas comuns

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_audit_logs'
down_revision: Union[str, None] = '001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Cria tabela core.audit_logs com estrutura completa.
    """
    
    # =====================================
    # Tabela core.audit_logs
    # =====================================
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('before', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('after', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='audit_logs_pkey'),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], name='audit_logs_user_id_fkey', ondelete='CASCADE'),
        sa.CheckConstraint("action IN ('create', 'update', 'delete')", name='check_audit_action'),
        sa.CheckConstraint("entity_type IN ('order', 'financial_entry', 'user')", name='check_audit_entity_type'),
        schema='core'
    )
    
    # =====================================
    # Índices de Performance
    # =====================================
    
    # Índice para consultas por usuário (quem fez?)
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], schema='core')
    
    # Índice composto para consultas por entidade (histórico de uma entidade específica)
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'], schema='core')
    
    # Índice para consultas por data (eventos recentes)
    op.create_index('ix_audit_logs_created_at', 'audit_logs', [sa.text('created_at DESC')], schema='core')
    
    # Índice para rastreamento de request (todas operações de uma requisição)
    op.create_index('ix_audit_logs_request_id', 'audit_logs', ['request_id'], schema='core')
    
    # =====================================
    # Comentários
    # =====================================
    # Comentários (1 op.execute por statement — psycopg v3 não aceita múltiplos)
    op.execute("COMMENT ON TABLE core.audit_logs IS 'Registro de auditoria de todas operações críticas do sistema'")
    op.execute("COMMENT ON COLUMN core.audit_logs.user_id IS 'Usuário que executou a ação'")
    op.execute("COMMENT ON COLUMN core.audit_logs.action IS 'Tipo de operação: create, update, delete'")
    op.execute("COMMENT ON COLUMN core.audit_logs.entity_type IS 'Tipo de entidade: order, financial_entry, user'")
    op.execute("COMMENT ON COLUMN core.audit_logs.entity_id IS 'ID da entidade afetada'")
    op.execute("COMMENT ON COLUMN core.audit_logs.before IS 'Estado anterior da entidade (NULL em create)'")
    op.execute("COMMENT ON COLUMN core.audit_logs.after IS 'Estado atual da entidade (NULL em delete)'")
    op.execute("COMMENT ON COLUMN core.audit_logs.request_id IS 'X-Request-ID do middleware para correlação'")
    op.execute("COMMENT ON COLUMN core.audit_logs.created_at IS 'Timestamp da operação'")


def downgrade() -> None:
    """
    Remove tabela audit_logs e índices.
    """
    op.execute("DROP INDEX IF EXISTS core.ix_audit_logs_request_id")
    op.execute("DROP INDEX IF EXISTS core.ix_audit_logs_created_at")
    op.execute("DROP INDEX IF EXISTS core.ix_audit_logs_entity")
    op.execute("DROP INDEX IF EXISTS core.ix_audit_logs_user_id")
    op.drop_table('audit_logs', schema='core')

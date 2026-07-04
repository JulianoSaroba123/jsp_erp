"""013_add_proposal_share_fields

Add share token fields to proposals table for public PDF sharing

Revision ID: 013_add_proposal_share_fields
Revises: 012_add_proposals_and_service_order_types
Create Date: 2026-03-13 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '013_add_proposal_share_fields'
down_revision = '012_add_proposals_and_service_order_types'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona campos para compartilhamento público de propostas (share link)
    """
    
    # Adicionar coluna share_token (token único para compartilhamento)
    op.add_column(
        'proposals',
        sa.Column('share_token', sa.String(length=64), nullable=True),
        schema='core'
    )
    
    # Adicionar coluna share_enabled (se compartilhamento está ativo)
    op.add_column(
        'proposals',
        sa.Column('share_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        schema='core'
    )
    
    # Adicionar coluna share_expires_at (data de expiração do link)
    op.add_column(
        'proposals',
        sa.Column('share_expires_at', sa.TIMESTAMP(), nullable=True),
        schema='core'
    )
    
    # Adicionar coluna share_created_at (quando o link foi gerado)
    op.add_column(
        'proposals',
        sa.Column('share_created_at', sa.TIMESTAMP(), nullable=True),
        schema='core'
    )
    
    # Criar índice único para share_token (para lookup rápido)
    op.create_index(
        'idx_proposals_share_token',
        'proposals',
        ['share_token'],
        unique=True,
        schema='core'
    )


def downgrade() -> None:
    """
    Remove campos de compartilhamento
    """
    
    # Remover índice
    op.drop_index('idx_proposals_share_token', table_name='proposals', schema='core')
    
    # Remover colunas
    op.drop_column('proposals', 'share_created_at', schema='core')
    op.drop_column('proposals', 'share_expires_at', schema='core')
    op.drop_column('proposals', 'share_enabled', schema='core')
    op.drop_column('proposals', 'share_token', schema='core')

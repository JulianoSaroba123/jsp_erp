"""add_settings_table

Revision ID: 6323d5edc547
Revises: 013_add_proposal_share_fields
Create Date: 2026-03-16 20:00:50.062530

Adiciona tabela core.settings para armazenar configurações do sistema.
Single-row table com ID fixo para garantir registro único.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6323d5edc547'
down_revision: Union[str, None] = '013_add_proposal_share_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Criar tabela core.settings e popular com dados do .env
    """
    # Criar tabela
    op.create_table(
        'settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("'00000000-0000-0000-0000-000000000001'::uuid"), nullable=False, comment='ID fixo para garantir registro único'),
        
        # Dados da Empresa
        sa.Column('company_name', sa.String(200), nullable=False, server_default='', comment='Razão Social'),
        sa.Column('trade_name', sa.String(200), nullable=True, comment='Nome Fantasia'),
        sa.Column('cnpj', sa.String(18), nullable=True, comment='CNPJ formatado'),
        sa.Column('email', sa.String(150), nullable=True, comment='Email principal'),
        sa.Column('phone', sa.String(20), nullable=True, comment='Telefone principal'),
        sa.Column('phone_2', sa.String(20), nullable=True, comment='Telefone secundário'),
        sa.Column('website', sa.String(200), nullable=True, comment='Website'),
        
        # Endereço
        sa.Column('cep', sa.String(10), nullable=True, comment='CEP'),
        sa.Column('street', sa.String(200), nullable=True, comment='Rua/Avenida'),
        sa.Column('number', sa.String(20), nullable=True, comment='Número'),
        sa.Column('neighborhood', sa.String(100), nullable=True, comment='Bairro'),
        sa.Column('city', sa.String(100), nullable=True, comment='Cidade'),
        sa.Column('state', sa.String(2), nullable=True, comment='Estado (UF)'),
        
        # Logo
        sa.Column('logo_url', sa.Text, nullable=True, comment='URL ou base64 da logo'),
        
        # Dados Bancários
        sa.Column('bank_name', sa.String(100), nullable=True, comment='Nome do banco'),
        sa.Column('bank_agency', sa.String(20), nullable=True, comment='Agência'),
        sa.Column('bank_account', sa.String(30), nullable=True, comment='Conta'),
        sa.Column('pix_key', sa.String(100), nullable=True, comment='Chave PIX'),
        
        # Institucional
        sa.Column('mission', sa.Text, nullable=True, comment='Missão da empresa'),
        sa.Column('vision', sa.Text, nullable=True, comment='Visão da empresa'),
        sa.Column('values', sa.Text, nullable=True, comment='Valores (comma-separated)'),
        
        # Configurações do Sistema
        sa.Column('theme', sa.String(10), nullable=False, server_default='light', comment='Tema: light ou dark'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='America/Sao_Paulo', comment='Timezone'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='BRL', comment='Moeda'),
        
        # PDF
        sa.Column('pdf_header_text', sa.Text, nullable=True, comment='Texto no cabeçalho do PDF'),
        sa.Column('pdf_footer_text', sa.Text, nullable=True, comment='Texto no rodapé do PDF'),
        sa.Column('default_proposal_message', sa.Text, nullable=True, comment='Mensagem padrão em propostas'),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('now()'), nullable=True),
        
        sa.PrimaryKeyConstraint('id', name='settings_pkey'),
        schema='core'
    )


def downgrade() -> None:
    """
    Remover tabela core.settings
    """
    op.drop_table('settings', schema='core')

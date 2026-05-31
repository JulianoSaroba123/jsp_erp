"""015 - Enhance service orders with advanced fields from legacy system

Revision ID: 015_enhance_service_orders
Revises: 014_enhance_financial
Create Date: 2026-04-05 14:00:00

Description:
    Adiciona campos avançados às ordens de serviço baseado no sistema legado:
    - Dual Mode (tipo_os: comercial/operacional)
    - Modo Operacional (tipo_servico: diaria/atendimento)
    - Controle de tempo detalhado (6 campos de horário + horas normais/extras)
    - Assinaturas digitais (cliente e técnico)
    - Integração com propostas (proposta_id)
    - Campo de local
    - Observações de anexos
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '015_enhance_service_orders'
down_revision = '014_enhance_financial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona campos avançados à tabela service_orders.
    """
    
    # ==================== DUAL MODE E OPERACIONAL ====================
    op.add_column('service_orders', 
        sa.Column('order_type', sa.String(20), nullable=False, server_default='comercial',
                  comment='comercial (com valores) ou operacional (controle interno)'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('service_type', sa.String(100), nullable=True,
                  comment='Para operacional: diaria ou atendimento'),
        schema='core'
    )
    
    # ==================== INTEGRAÇÃO COM PROPOSTAS ====================
    op.add_column('service_orders', 
        sa.Column('proposal_id', UUID(as_uuid=True), nullable=True,
                  comment='Proposta que originou esta OS (opcional)'),
        schema='core'
    )
    
    # Criar FK para proposals (se existir)
    try:
        op.create_foreign_key(
            'fk_service_orders_proposal_id',
            'service_orders', 'proposals',
            ['proposal_id'], ['id'],
            source_schema='core', referent_schema='core',
            ondelete='SET NULL'
        )
    except Exception:
        # Se falhar, ignorar (pode ser criada manualmente depois)
        pass
    
    op.create_index('ix_service_orders_proposal_id', 'service_orders', ['proposal_id'], schema='core')
    
    # ==================== CAMPO DE LOCAL ====================
    op.add_column('service_orders', 
        sa.Column('location', sa.String(200), nullable=True,
                  comment='Local onde o serviço foi realizado'),
        schema='core'
    )
    
    # ==================== CONTROLE DE TEMPO DETALHADO (6 CAMPOS) ====================
    # Sistema de controle de jornada completa
    op.add_column('service_orders', 
        sa.Column('morning_entry_time', sa.Time, nullable=True,
                  comment='Hora de entrada pela manhã'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('lunch_exit_time', sa.Time, nullable=True,
                  comment='Hora de saída para almoço'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('lunch_return_time', sa.Time, nullable=True,
                  comment='Hora de retorno do almoço'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('evening_exit_time', sa.Time, nullable=True,
                  comment='Hora de saída no final do período'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('overtime_entry_time', sa.Time, nullable=True,
                  comment='Hora de entrada para horas extras (opcional)'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('overtime_exit_time', sa.Time, nullable=True,
                  comment='Hora de saída após horas extras (opcional)'),
        schema='core'
    )
    
    # ==================== HORAS CALCULADAS ====================
    op.add_column('service_orders', 
        sa.Column('regular_hours', sa.Numeric(10, 2), nullable=True,
                  comment='Horas normais trabalhadas (formato decimal)'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('overtime_hours', sa.Numeric(10, 2), nullable=True,
                  comment='Horas extras trabalhadas (formato decimal)'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('lunch_break_minutes', sa.Integer, nullable=True, server_default='60',
                  comment='Intervalo de almoço em minutos'),
        schema='core'
    )
    
    # ==================== ASSINATURAS DIGITAIS ====================
    # Assinatura do Cliente
    op.add_column('service_orders', 
        sa.Column('customer_signature', sa.Text, nullable=True,
                  comment='Assinatura do cliente em base64'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('customer_signature_name', sa.String(200), nullable=True,
                  comment='Nome de quem assinou (cliente)'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('customer_signature_date', sa.DateTime, nullable=True,
                  comment='Data/hora da assinatura do cliente'),
        schema='core'
    )
    
    # Assinatura do Técnico
    op.add_column('service_orders', 
        sa.Column('technician_signature', sa.Text, nullable=True,
                  comment='Assinatura do técnico em base64'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('technician_signature_name', sa.String(200), nullable=True,
                  comment='Nome do técnico que assinou'),
        schema='core'
    )
    
    op.add_column('service_orders', 
        sa.Column('technician_signature_date', sa.DateTime, nullable=True,
                  comment='Data/hora da assinatura do técnico'),
        schema='core'
    )
    
    # ==================== OBSERVAÇÕES DE ANEXOS ====================
    op.add_column('service_orders', 
        sa.Column('attachments_notes', sa.Text, nullable=True,
                  comment='Observações sobre os anexos'),
        schema='core'
    )
    
    # ==================== ÍNDICES ADICIONAIS ====================
    op.create_index('ix_service_orders_order_type', 'service_orders', ['order_type'], schema='core')
    op.create_index('ix_service_orders_service_type', 'service_orders', ['service_type'], schema='core')


def downgrade() -> None:
    """
    Remove os campos avançados adicionados.
    """
    
    # Remove índices
    op.drop_index('ix_service_orders_service_type', table_name='service_orders', schema='core')
    op.drop_index('ix_service_orders_order_type', table_name='service_orders', schema='core')
    op.drop_index('ix_service_orders_proposal_id', table_name='service_orders', schema='core')
    
    # Remove FK de proposal
    try:
        op.drop_constraint('fk_service_orders_proposal_id', 'service_orders', schema='core', type_='foreignkey')
    except Exception:
        pass
    
    # Remove colunas (ordem reversa)
    op.drop_column('service_orders', 'attachments_notes', schema='core')
    
    op.drop_column('service_orders', 'technician_signature_date', schema='core')
    op.drop_column('service_orders', 'technician_signature_name', schema='core')
    op.drop_column('service_orders', 'technician_signature', schema='core')
    
    op.drop_column('service_orders', 'customer_signature_date', schema='core')
    op.drop_column('service_orders', 'customer_signature_name', schema='core')
    op.drop_column('service_orders', 'customer_signature', schema='core')
    
    op.drop_column('service_orders', 'lunch_break_minutes', schema='core')
    op.drop_column('service_orders', 'overtime_hours', schema='core')
    op.drop_column('service_orders', 'regular_hours', schema='core')
    
    op.drop_column('service_orders', 'overtime_exit_time', schema='core')
    op.drop_column('service_orders', 'overtime_entry_time', schema='core')
    op.drop_column('service_orders', 'evening_exit_time', schema='core')
    op.drop_column('service_orders', 'lunch_return_time', schema='core')
    op.drop_column('service_orders', 'lunch_exit_time', schema='core')
    op.drop_column('service_orders', 'morning_entry_time', schema='core')
    
    op.drop_column('service_orders', 'location', schema='core')
    op.drop_column('service_orders', 'proposal_id', schema='core')
    op.drop_column('service_orders', 'service_type', schema='core')
    op.drop_column('service_orders', 'order_type', schema='core')

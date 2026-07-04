"""create service orders tables

Revision ID: 011_create_service_orders
Revises: 010_create_suppliers
Create Date: 2026-03-09 00:00:00.000000

Cria 5 tabelas para o módulo de Ordem de Serviço:
1. service_orders - Tabela principal
2. service_order_items - Serviços realizados
3. service_order_products - Produtos/peças utilizados
4. service_order_installments - Parcelas de pagamento
5. service_order_attachments - Anexos (imagens, PDFs, documentos)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '011_create_service_orders'
down_revision = '010_create_suppliers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Cria módulo completo de Ordens de Serviço com 5 tabelas relacionadas.
    """
    
    # ==================== 1. SERVICE_ORDERS (Tabela Principal) ====================
    op.create_table(
        'service_orders',
        
        # PK
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Número da OS (gerado automaticamente: OS2025001, etc)
        sa.Column('number', sa.String(20), unique=True, nullable=False, comment='Número da OS (formato: OS2025001)'),
        
        # Cliente (FK)
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('core.customers.id'), nullable=False, comment='Cliente'),
        
        # Dados básicos
        sa.Column('title', sa.String(200), nullable=False, comment='Título da ordem de serviço'),
        sa.Column('description', sa.Text, nullable=True, comment='Descrição detalhada'),
        
        # Solicitação
        sa.Column('requester', sa.String(200), nullable=True, comment='Nome do solicitante'),
        sa.Column('problem_description', sa.Text, nullable=True, comment='Descrição do problema'),
        
        # Status e Prioridade
        sa.Column('status', sa.String(20), nullable=False, default='pendente', comment='pendente, em_execucao, finalizada, cancelada'),
        sa.Column('priority', sa.String(20), nullable=False, default='normal', comment='baixa, normal, alta, urgente'),
        
        # Datas
        sa.Column('opening_date', sa.Date, nullable=False, server_default=sa.text('CURRENT_DATE'), comment='Data de abertura'),
        sa.Column('expected_date', sa.Date, nullable=True, comment='Data prevista para conclusão'),
        sa.Column('start_date', sa.DateTime, nullable=True, comment='Data/hora de início'),
        sa.Column('completion_date', sa.DateTime, nullable=True, comment='Data/hora de conclusão'),
        
        # Responsável
        sa.Column('technician', sa.String(100), nullable=True, comment='Técnico responsável'),
        
        # Equipamento
        sa.Column('equipment', sa.String(200), nullable=True, comment='Equipamento'),
        sa.Column('brand_model', sa.String(200), nullable=True, comment='Marca/Modelo'),
        sa.Column('serial_number', sa.String(100), nullable=True, comment='Número de série'),
        
        # Descrições técnicas
        sa.Column('reported_defect', sa.Text, nullable=True, comment='Defeito relatado'),
        sa.Column('technical_diagnosis', sa.Text, nullable=True, comment='Diagnóstico técnico'),
        sa.Column('solution', sa.Text, nullable=True, comment='Solução aplicada'),
        sa.Column('notes', sa.Text, nullable=True, comment='Observações gerais'),
        
        # Controle de tempo
        sa.Column('start_time', sa.Time, nullable=True, comment='Hora inicial'),
        sa.Column('end_time', sa.Time, nullable=True, comment='Hora final'),
        sa.Column('total_hours', sa.String(20), nullable=True, comment='Total de horas (formato: 2h 30min)'),
        
        # Controle de KM
        sa.Column('initial_km', sa.Integer, nullable=True, comment='KM inicial'),
        sa.Column('final_km', sa.Integer, nullable=True, comment='KM final'),
        sa.Column('total_km', sa.String(20), nullable=True, comment='Total KM (formato: 15.5 km)'),
        
        # Valores
        sa.Column('service_amount', sa.Numeric(10, 2), nullable=False, default=0.00, comment='Valor dos serviços'),
        sa.Column('parts_amount', sa.Numeric(10, 2), nullable=False, default=0.00, comment='Valor das peças'),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, default=0.00, comment='Desconto'),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False, default=0.00, comment='Valor total'),
        
        # Garantia
        sa.Column('warranty_days', sa.Integer, nullable=True, default=0, comment='Dias de garantia'),
        
        # Condições de pagamento
        sa.Column('payment_condition', sa.String(50), nullable=False, default='a_vista', comment='a_vista ou parcelado'),
        sa.Column('installment_count', sa.Integer, nullable=True, default=1, comment='Número de parcelas'),
        sa.Column('down_payment', sa.Numeric(10, 2), nullable=True, default=0.00, comment='Valor de entrada'),
        sa.Column('first_installment_date', sa.Date, nullable=True, comment='Data da primeira parcela'),
        sa.Column('payment_due_date', sa.Date, nullable=True, comment='Data de vencimento (à vista)'),
        sa.Column('payment_description', sa.Text, nullable=True, comment='Descrição do pagamento'),
        sa.Column('payment_status', sa.String(20), nullable=False, default='pendente', comment='pendente, parcial, pago, vencido'),
        
        # Preferências
        sa.Column('include_images_in_report', sa.Boolean, default=False, comment='Incluir imagens no relatório PDF'),
        
        # Auditoria
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, onupdate=sa.text('now()')),
        
        # Soft Delete
        sa.Column('deleted_at', sa.TIMESTAMP, nullable=True),
        
        schema='core'
    )
    
    # Índices para service_orders
    op.create_index('ix_service_orders_number', 'service_orders', ['number'], unique=True, schema='core')
    op.create_index('ix_service_orders_customer_id', 'service_orders', ['customer_id'], schema='core')
    op.create_index('ix_service_orders_status', 'service_orders', ['status'], schema='core')
    op.create_index('ix_service_orders_priority', 'service_orders', ['priority'], schema='core')
    op.create_index('ix_service_orders_deleted_at', 'service_orders', ['deleted_at'], schema='core')
    op.create_index('ix_service_orders_opening_date', 'service_orders', ['opening_date'], schema='core')
    
    
    # ==================== 2. SERVICE_ORDER_ITEMS (Serviços Realizados) ====================
    op.create_table(
        'service_order_items',
        
        # PK
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # FK
        sa.Column('service_order_id', UUID(as_uuid=True), sa.ForeignKey('core.service_orders.id', ondelete='CASCADE'), nullable=False),
        
        # Dados do serviço
        sa.Column('description', sa.String(200), nullable=False, comment='Descrição do serviço'),
        sa.Column('service_type', sa.String(20), nullable=False, default='hora', comment='hora, dia, fechado'),
        sa.Column('quantity', sa.Numeric(5, 2), nullable=False, default=1.00, comment='Quantidade'),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False, default=0.00, comment='Valor unitário'),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False, default=0.00, comment='Valor total'),
        
        # Auditoria
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()'), nullable=False),
        
        schema='core'
    )
    
    op.create_index('ix_service_order_items_service_order_id', 'service_order_items', ['service_order_id'], schema='core')
    
    
    # ==================== 3. SERVICE_ORDER_PRODUCTS (Produtos/Peças) ====================
    op.create_table(
        'service_order_products',
        
        # PK
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # FK para service_order
        sa.Column('service_order_id', UUID(as_uuid=True), sa.ForeignKey('core.service_orders.id', ondelete='CASCADE'), nullable=False),
        
        # FK para product (será criada separadamente após verificar que products existe)
        sa.Column('product_id', UUID(as_uuid=True), nullable=True, comment='Produto cadastrado (opcional)'),
        
        # Dados do produto
        sa.Column('description', sa.String(200), nullable=False, comment='Descrição do produto/peça'),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False, default=1.000, comment='Quantidade'),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False, default=0.00, comment='Valor unitário'),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False, default=0.00, comment='Valor total'),
        
        # Auditoria
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()'), nullable=False),
        
        schema='core'
    )
    
    op.create_index('ix_service_order_products_service_order_id', 'service_order_products', ['service_order_id'], schema='core')
    op.create_index('ix_service_order_products_product_id', 'service_order_products', ['product_id'], schema='core')
    
    # Criar FK para products separadamente (mais seguro)
    try:
        op.create_foreign_key(
            'fk_service_order_products_product_id',
            'service_order_products', 'products',
            ['product_id'], ['id'],
            source_schema='core', referent_schema='core'
        )
    except Exception:
        # Se falhar, ignorar (pode ser criada manualmente depois)
        pass
    
    
    # ==================== 4. SERVICE_ORDER_INSTALLMENTS (Parcelas) ====================
    op.create_table(
        'service_order_installments',
        
        # PK
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # FK
        sa.Column('service_order_id', UUID(as_uuid=True), sa.ForeignKey('core.service_orders.id', ondelete='CASCADE'), nullable=False),
        
        # Dados da parcela
        sa.Column('installment_number', sa.Integer, nullable=False, comment='Número da parcela'),
        sa.Column('due_date', sa.Date, nullable=False, comment='Data de vencimento'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False, comment='Valor da parcela'),
        sa.Column('paid', sa.Boolean, nullable=False, default=False, comment='Pago?'),
        sa.Column('payment_date', sa.Date, nullable=True, comment='Data do pagamento'),
        
        # Auditoria
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()'), nullable=False),
        
        schema='core'
    )
    
    op.create_index('ix_service_order_installments_service_order_id', 'service_order_installments', ['service_order_id'], schema='core')
    op.create_index('ix_service_order_installments_due_date', 'service_order_installments', ['due_date'], schema='core')
    
    
    # ==================== 5. SERVICE_ORDER_ATTACHMENTS (Anexos) ====================
    op.create_table(
        'service_order_attachments',
        
        # PK
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # FK
        sa.Column('service_order_id', UUID(as_uuid=True), sa.ForeignKey('core.service_orders.id', ondelete='CASCADE'), nullable=False),
        
        # Dados do arquivo
        sa.Column('original_filename', sa.String(255), nullable=False, comment='Nome original do arquivo'),
        sa.Column('stored_filename', sa.String(255), nullable=False, comment='Nome salvo no servidor'),
        sa.Column('file_type', sa.String(50), nullable=False, comment='image, document, pdf'),
        sa.Column('mime_type', sa.String(100), nullable=True, comment='Tipo MIME'),
        sa.Column('file_size', sa.Integer, nullable=True, comment='Tamanho em bytes'),
        sa.Column('file_path', sa.String(500), nullable=True, comment='Caminho no filesystem'),
        sa.Column('file_content', sa.LargeBinary, nullable=True, comment='Conteúdo em BLOB (para cloud)'),
        
        # Auditoria
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()'), nullable=False),
        
        schema='core'
    )
    
    op.create_index('ix_service_order_attachments_service_order_id', 'service_order_attachments', ['service_order_id'], schema='core')


def downgrade() -> None:
    """
    Remove todas as 5 tabelas do módulo de Ordem de Serviço.
    Ordem reversa da criação para respeitar constraints de FK.
    """
    
    # Remove tabelas na ordem reversa (filho antes do pai)
    op.drop_table('service_order_attachments', schema='core')
    op.drop_table('service_order_installments', schema='core')
    op.drop_table('service_order_products', schema='core')
    op.drop_table('service_order_items', schema='core')
    op.drop_table('service_orders', schema='core')

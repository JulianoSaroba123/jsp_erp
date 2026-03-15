"""
Model SQLAlchemy para ordens de serviço e tabelas relacionadas.

Tabelas:
- core.service_orders: Dados principais da ordem de serviço
- core.service_order_items: Serviços realizados (hora/dia/fechado)
- core.service_order_products: Produtos/peças utilizados
- core.service_order_installments: Parcelas de pagamento
- core.service_order_attachments: Anexos (imagens, PDFs, documentos)
"""
from sqlalchemy import (
    Column, String, Text, TIMESTAMP, Date, Time, DateTime, Integer, 
    Numeric, Boolean, ForeignKey, LargeBinary, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ServiceOrder(Base):
    """
    Tabela principal de ordens de serviço.
    Schema: core
    
    Controla todo o ciclo de vida das ordens de serviço,
    desde a abertura até a conclusão.
    """
    __tablename__ = "service_orders"
    __table_args__ = {"schema": "core"}

    # PK
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # Número da OS (formato: OS2025001, OS2025002...)
    number = Column(String(20), unique=True, nullable=False, index=True)
    
    # ========== TIPO DE ORDEM DE SERVIÇO ==========
    # NEW: tipo_ordem determina o comportamento da OS
    tipo_ordem = Column(
        String(20),
        nullable=False,
        default='atendimento',
        index=True
    )  # 'atendimento' (emergencial, cobrado) ou 'projeto' (acompanhamento de proposta aprovada)
    
    # NEW: controla se valores devem ser exibidos no relatório/PDF
    # - atendimento: True (mostra valores para cobrança)
    # - projeto: False (oculta valores, foco em execução técnica)
    exibir_valores = Column(
        Boolean,
        nullable=False,
        default=True
    )
    
    # NEW: vínculo opcional com proposta aprovada
    # Quando uma proposta é aprovada e gera uma OS de projeto, este campo é preenchido
    proposta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.proposals.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # NEW: controle de andamento para OS de projeto
    percentual_concluido = Column(
        Integer,
        nullable=False,
        default=0  # 0 a 100
    )
    
    # NEW: etapa atual do projeto (ex: "Instalação de cabos", "Configuração de rede")
    etapa_atual = Column(
        String(200),
        nullable=True
    )
    # ===============================================
    
    # Cliente (FK para customers)
    customer_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("core.customers.id"), 
        nullable=False,
        index=True
    )
    
    # Dados básicos
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Solicitação
    requester = Column(String(200), nullable=True)  # Nome do solicitante
    problem_description = Column(Text, nullable=True)  # Descrição do problema
    
    # Status (pendente, em_execucao, finalizada, cancelada)
    status = Column(
        String(20), 
        nullable=False, 
        default='pendente',
        index=True
    )
    
    # Prioridade (baixa, normal, alta, urgente)
    priority = Column(
        String(20), 
        nullable=False, 
        default='normal'
    )
    
    # Datas
    opening_date = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    expected_date = Column(Date, nullable=True)
    start_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    
    # Responsável
    technician = Column(String(100), nullable=True)
    
    # Equipamento
    equipment = Column(String(200), nullable=True)
    brand_model = Column(String(200), nullable=True)
    serial_number = Column(String(100), nullable=True)
    
    # Descrições técnicas
    reported_defect = Column(Text, nullable=True)
    technical_diagnosis = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Controle de tempo
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    total_hours = Column(String(20), nullable=True)  # Formato: "2h 30min"
    
    # Controle de KM
    initial_km = Column(Integer, nullable=True)
    final_km = Column(Integer, nullable=True)
    total_km = Column(String(20), nullable=True)  # Formato: "15.5 km"
    
    # Valores (armazenados em centavos para evitar problemas de precisão)
    service_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    parts_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Garantia (em dias)
    warranty_days = Column(Integer, nullable=True, default=0)
    
    # Condições de pagamento
    payment_condition = Column(
        String(50), 
        nullable=False, 
        default='a_vista'
    )  # a_vista, parcelado
    installment_count = Column(Integer, nullable=True, default=1)
    down_payment = Column(Numeric(10, 2), nullable=True, default=0.00)
    first_installment_date = Column(Date, nullable=True)
    payment_due_date = Column(Date, nullable=True)
    payment_description = Column(Text, nullable=True)
    payment_status = Column(
        String(20), 
        nullable=False, 
        default='pendente'
    )  # pendente, parcial, pago, vencido
    
    # Preferência de relatório
    include_images_in_report = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, onupdate=text("now()"))
    
    # Soft Delete
    deleted_at = Column(TIMESTAMP, nullable=True, index=True)
    
    # Relationships
    proposal = relationship(
        "Proposal",
        foreign_keys=[proposta_id],
        back_populates="service_orders",
        lazy="joined"  # Carregar proposta automaticamente quando carregar OS
    )
    items = relationship(
        "ServiceOrderItem",
        back_populates="service_order",
        cascade="all, delete-orphan"
    )
    products = relationship(
        "ServiceOrderProduct",
        back_populates="service_order",
        cascade="all, delete-orphan"
    )
    installments = relationship(
        "ServiceOrderInstallment",
        back_populates="service_order",
        cascade="all, delete-orphan",
        order_by="ServiceOrderInstallment.installment_number"
    )
    attachments = relationship(
        "ServiceOrderAttachment",
        back_populates="service_order",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ServiceOrder(id={self.id}, number={self.number})>"


class ServiceOrderItem(Base):
    """
    Tabela de itens de serviço da ordem.
    Schema: core
    
    Representa cada serviço realizado com tipo (hora/dia/fechado),
    quantidade, valor unitário e total.
    """
    __tablename__ = "service_order_items"
    __table_args__ = {"schema": "core"}

    # PK
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # FK para service_orders
    service_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.service_orders.id"),
        nullable=False,
        index=True
    )
    
    # Dados do serviço
    description = Column(String(200), nullable=False)
    service_type = Column(
        String(20), 
        nullable=False, 
        default='hora'
    )  # hora, dia, fechado
    quantity = Column(Numeric(5, 2), nullable=False, default=1.00)
    unit_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    
    # Relationship
    service_order = relationship("ServiceOrder", back_populates="items")

    def __repr__(self):
        return f"<ServiceOrderItem(id={self.id}, description={self.description})>"


class ServiceOrderProduct(Base):
    """
    Tabela de produtos utilizados na ordem de serviço.
    Schema: core
    
    Representa produtos/peças utilizados na execução do serviço.
    """
    __tablename__ = "service_order_products"
    __table_args__ = {"schema": "core"}

    # PK
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # FK para service_orders
    service_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.service_orders.id"),
        nullable=False,
        index=True
    )
    
    # FK para products (opcional - pode ser produto não cadastrado)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.products.id"),
        nullable=True
    )
    
    # Dados do produto
    description = Column(String(200), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False, default=1.000)
    unit_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    
    # Relationship
    service_order = relationship("ServiceOrder", back_populates="products")

    def __repr__(self):
        return f"<ServiceOrderProduct(id={self.id}, description={self.description})>"


class ServiceOrderInstallment(Base):
    """
    Tabela de parcelas da ordem de serviço.
    Schema: core
    
    Quando a ordem é parcelada, cada parcela tem sua data
    de vencimento e valor.
    """
    __tablename__ = "service_order_installments"
    __table_args__ = {"schema": "core"}

    # PK
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # FK para service_orders
    service_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.service_orders.id"),
        nullable=False,
        index=True
    )
    
    # Dados da parcela
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    paid = Column(Boolean, nullable=False, default=False)
    payment_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    
    # Relationship
    service_order = relationship("ServiceOrder", back_populates="installments")

    def __repr__(self):
        return f"<ServiceOrderInstallment(id={self.id}, number={self.installment_number})>"


class ServiceOrderAttachment(Base):
    """
    Tabela de anexos da ordem de serviço.
    Schema: core
    
    Armazena informações sobre arquivos anexados à ordem de serviço
    (imagens, documentos, PDFs, etc.).
    """
    __tablename__ = "service_order_attachments"
    __table_args__ = {"schema": "core"}

    # PK
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # FK para service_orders
    service_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.service_orders.id"),
        nullable=False,
        index=True
    )
    
    # Dados do arquivo
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)  # Nome salvo no servidor
    file_type = Column(String(50), nullable=False)  # image, document, pdf
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)  # em bytes
    file_path = Column(String(500), nullable=True)  # Caminho no filesystem
    file_content = Column(LargeBinary, nullable=True)  # Conteúdo em BLOB (para cloud)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    
    # Relationship
    service_order = relationship("ServiceOrder", back_populates="attachments")

    def __repr__(self):
        return f"<ServiceOrderAttachment(id={self.id}, filename={self.original_filename})>"

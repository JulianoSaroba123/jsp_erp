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
    code = Column(String(20), unique=True, nullable=True, index=True)
    
    # ========== DUAL MODE (COMERCIAL/OPERACIONAL) ==========
    # Tipo de OS: comercial (com valores financeiros) ou operacional (controle interno)
    order_type = Column(
        String(20),
        nullable=False,
        default='comercial',
        index=True
    )  # 'comercial' ou 'operacional'
    
    # Tipo de serviço (para operacional): 'diaria' ou 'atendimento'
    service_type = Column(
        String(100),
        nullable=True,
        index=True
    )
    
    # ========== INTEGRAÇÃO COM PROPOSTAS ==========
    # Vínculo opcional com proposta aprovada
    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.proposals.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # ========== LOCAL ==========
    location = Column(String(200), nullable=True)
    
    # Cliente (FK para customers)
    customer_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("core.customers.id"), 
        nullable=False,
        index=True
    )
    
    # Usuário que criou a OS
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id"),
        nullable=False,
        index=True
    )
    
    # Dados básicos
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    technical_report = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)

    # Snapshot do cliente para auditoria e impressão
    client_name = Column(String(200), nullable=True)
    client_document = Column(String(30), nullable=True)
    client_phone = Column(String(30), nullable=True)
    client_email = Column(String(255), nullable=True)
    client_address = Column(Text, nullable=True)
    
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
    opening_date = Column(Date, nullable=True)  # Removido server_default para match com banco
    scheduled_date = Column(Date, nullable=True)
    expected_date = Column(Date, nullable=True)
    start_date = Column(DateTime, nullable=True)
    completed_date = Column(Date, nullable=True)
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

    # Condicoes de pagamento
    payment_condition = Column(String(50), nullable=False, default="a_vista")
    installment_count = Column(Integer, nullable=True, default=1)
    down_payment = Column(Numeric(10, 2), nullable=True, default=0.00)
    first_installment_date = Column(Date, nullable=True)
    payment_due_date = Column(Date, nullable=True)
    payment_description = Column(Text, nullable=True)
    payment_status = Column(String(20), nullable=False, default="pendente")
    payment_method = Column(String(50), nullable=True)
    include_images_in_report = Column(Boolean, default=False)

    # Totais enterprise
    total_services = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_products = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_displacement = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_discount = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_amount_enterprise = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Datas enterprise
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # ========== CONTROLE DE TEMPO DETALHADO (6 CAMPOS) ==========
    morning_entry_time = Column(Time, nullable=True)  # Hora de entrada pela manhã
    lunch_exit_time = Column(Time, nullable=True)  # Hora de saída para almoço
    lunch_return_time = Column(Time, nullable=True)  # Hora de retorno do almoço
    evening_exit_time = Column(Time, nullable=True)  # Hora de saída no final do período
    overtime_entry_time = Column(Time, nullable=True)  # Hora de entrada para horas extras (opcional)
    overtime_exit_time = Column(Time, nullable=True)  # Hora de saída após horas extras (opcional)
    
    # Horas calculadas
    regular_hours = Column(Numeric(10, 2), nullable=True)  # Horas normais em formato decimal
    overtime_hours = Column(Numeric(10, 2), nullable=True)  # Horas extras em formato decimal
    lunch_break_minutes = Column(Integer, nullable=True, default=60)  # Intervalo de almoço em minutos
    
    # ========== ASSINATURAS DIGITAIS ==========
    # Assinatura do Cliente
    customer_signature = Column(Text, nullable=True)  # Assinatura em base64
    customer_signature_name = Column(String(200), nullable=True)  # Nome de quem assinou
    customer_signature_date = Column(DateTime, nullable=True)  # Data/hora da assinatura
    
    # Assinatura do Técnico
    technician_signature = Column(Text, nullable=True)  # Assinatura em base64
    technician_signature_name = Column(String(200), nullable=True)  # Nome do técnico que assinou
    technician_signature_date = Column(DateTime, nullable=True)  # Data/hora da assinatura
    
    # ========== OBSERVAÇÕES DE ANEXOS ==========
    attachments_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, onupdate=text("now()"))
    
    # Soft Delete
    deleted_at = Column(TIMESTAMP, nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    customer = relationship(
        "Customer",
        foreign_keys=[customer_id],
        lazy="joined"
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined"
    )
    proposal = relationship(
        "Proposal",
        foreign_keys=[proposal_id],
        back_populates="service_orders",
        lazy="select"  # Mudado de joined para select para evitar eager load
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
    equipments = relationship(
        "ServiceOrderEquipment",
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

    # ========== PROPERTIES INTELIGENTES (do sistema legado) ==========
    
    @property
    def customer_name(self) -> str:
        """Nome do cliente para listagens e respostas da API."""
        return self.customer.name if self.customer else ""

    @property
    def status_formatado(self) -> str:
        """Retorna status formatado para exibição."""
        status_map = {
            'pendente': 'Pendente',
            'em_execucao': 'Em Execução',
            'finalizada': 'Finalizada',
            'cancelada': 'Cancelada'
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def prioridade_formatada(self) -> str:
        """Retorna prioridade formatada para exibição."""
        prioridade_map = {
            'baixa': 'Baixa',
            'normal': 'Normal',
            'alta': 'Alta',
            'urgente': 'Urgente'
        }
        return prioridade_map.get(self.priority, self.priority.title())
    
    @property
    def tipo_os_formatado(self) -> str:
        """Retorna tipo de OS formatado para exibição."""
        tipo_map = {
            'comercial': 'Comercial - Com valores financeiros',
            'operacional': 'Operacional - Apenas controle interno'
        }
        return tipo_map.get(self.order_type, self.order_type.title())
    
    @property
    def eh_operacional(self) -> bool:
        """Verifica se a OS é do tipo operacional (sem valores)."""
        return self.order_type == 'operacional'
    
    @property
    def eh_comercial(self) -> bool:
        """Verifica se a OS é do tipo comercial (com valores)."""
        return self.order_type == 'comercial'
    
    @property
    def modo_operacional(self) -> str:
        """Retorna o modo operacional padronizado da OS."""
        if self.order_type != 'operacional':
            return 'atendimento'
        return 'diaria' if (self.service_type or '').lower() == 'diaria' else 'atendimento'
    
    @property
    def eh_diaria(self) -> bool:
        """Indica se a OS operacional está em modo diária."""
        return self.modo_operacional == 'diaria'
    
    @property
    def eh_atendimento(self) -> bool:
        """Indica se a OS está em modo atendimento."""
        return self.modo_operacional == 'atendimento'
    
    @property
    def km_total(self) -> int:
        """Calcula KM total percorrido."""
        if self.initial_km and self.final_km and self.final_km > self.initial_km:
            return self.final_km - self.initial_km
        return 0
    
    @property
    def tempo_total_decimal(self) -> float:
        """Calcula tempo total em decimal (horas)."""
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            
            # Converte time para datetime para cálculo
            hoje = datetime.today().date()
            inicio = datetime.combine(hoje, self.start_time)
            fim = datetime.combine(hoje, self.end_time)
            
            # Se hora final for menor, assume que passou para o dia seguinte
            if fim < inicio:
                fim += timedelta(days=1)
            
            diferenca = fim - inicio
            return diferenca.total_seconds() / 3600  # converte para horas
        return 0
    
    @property
    def tempo_total_formatado(self) -> str:
        """Retorna tempo total formatado (HH:MM)."""
        tempo_decimal = self.tempo_total_decimal
        if tempo_decimal > 0:
            horas = int(tempo_decimal)
            minutos = int((tempo_decimal - horas) * 60)
            return f"{horas:02d}:{minutos:02d}"
        return "00:00"
    
    @property
    def valor_total_servicos(self):
        """Calcula valor total dos serviços."""
        from decimal import Decimal
        if not self.items:
            return Decimal('0')
        total = sum(float(item.total_price or 0) for item in self.items)
        return Decimal(str(total))
    
    @property
    def valor_total_produtos(self):
        """Calcula valor total dos produtos."""
        from decimal import Decimal
        if not self.products:
            return Decimal('0')
        total = sum(float(produto.total_price or 0) for produto in self.products)
        return Decimal(str(total))
    
    @property
    def valor_total_calculado(self):
        """Calcula valor total (serviços + produtos - desconto)."""
        from decimal import Decimal
        servicos = Decimal(str(self.valor_total_servicos or 0))
        produtos = Decimal(str(self.valor_total_produtos or 0))
        desconto = Decimal(str(self.discount_amount or 0))
        total = servicos + produtos - desconto
        return float(total)
    
    @property
    def status_cor(self) -> str:
        """Retorna cor do status para exibição."""
        cores = {
            'pendente': 'warning',
            'em_execucao': 'primary',
            'finalizada': 'success',
            'cancelada': 'danger'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def prioridade_cor(self) -> str:
        """Retorna cor da prioridade para exibição."""
        cores = {
            'baixa': 'success',
            'normal': 'secondary',
            'alta': 'warning',
            'urgente': 'danger'
        }
        return cores.get(self.priority, 'secondary')
    
    @property
    def prazo_vencido(self) -> bool:
        """Verifica se o prazo está vencido."""
        from datetime import date
        if not self.expected_date or self.status in ['finalizada', 'cancelada']:
            return False
        return date.today() > self.expected_date
    
    @property
    def dias_em_aberto(self) -> int:
        """Calcula quantos dias a OS está em aberto."""
        from datetime import date
        if self.status in ['finalizada', 'cancelada']:
            return 0
        return (date.today() - self.opening_date).days if self.opening_date else 0
    
    @property
    def horas_normais_formatado(self) -> str:
        """Retorna horas normais formatadas (ex: '8h 30min')."""
        if not self.regular_hours:
            return '0h'
        try:
            horas_decimal = float(self.regular_hours)
            horas_inteiras = int(horas_decimal)
            minutos = int((horas_decimal - horas_inteiras) * 60)
            return f'{horas_inteiras}h {minutos}min' if minutos > 0 else f'{horas_inteiras}h'
        except (ValueError, TypeError):
            return str(self.regular_hours)
    
    @property
    def horas_extras_formatado(self) -> str:
        """Retorna horas extras formatadas (ex: '2h 30min')."""
        if not self.overtime_hours:
            return '0h'
        try:
            horas_decimal = float(self.overtime_hours)
            horas_inteiras = int(horas_decimal)
            minutos = int((horas_decimal - horas_inteiras) * 60)
            return f'{horas_inteiras}h {minutos}min' if minutos > 0 else f'{horas_inteiras}h'
        except (ValueError, TypeError):
            return str(self.overtime_hours)
    
    @classmethod
    def gerar_proximo_numero(cls, db_session):
        """
        Gera o próximo número de OS no formato OS2026001, OS2026002, etc.
        
        Sistema inteligente que:
        - Usa o ano atual
        - Busca o maior número existente
        - Garante sequência sem duplicatas
        - Formato: OS + ANO + SEQUENCIAL (4 dígitos)
        """
        from datetime import date
        from sqlalchemy import text
        
        ano_atual = date.today().year
        prefixo = f"OS{ano_atual}"
        
        try:
            # Query raw SQL compatível com PostgreSQL
            sql = text("""
                SELECT number 
                FROM core.service_orders 
                WHERE number LIKE :prefixo AND deleted_at IS NULL
                ORDER BY number DESC 
                LIMIT 1
            """)
            
            result = db_session.execute(sql, {"prefixo": f"{prefixo}%"})
            ultima_os = result.first()
            
            maior_numero = 0
            
            if ultima_os:
                try:
                    numero_str = ultima_os[0]  # Pega o primeiro campo do resultado
                    # Extrai apenas a parte numérica (remove "OS2026")
                    parte_numerica = numero_str.replace(prefixo, "")
                    if parte_numerica.isdigit():
                        maior_numero = int(parte_numerica)
                except (ValueError, AttributeError, IndexError):
                    maior_numero = 0
            
            # Próximo número é sempre maior + 1
            proximo_numero = maior_numero + 1
            numero_os = f"{prefixo}{proximo_numero:04d}"
            
            # Verificação de segurança contra duplicatas
            tentativas = 0
            while tentativas < 100:
                check_sql = text("SELECT COUNT(*) FROM core.service_orders WHERE number = :numero")
                count_result = db_session.execute(check_sql, {"numero": numero_os})
                count = count_result.scalar()
                
                if count == 0:
                    break
                    
                proximo_numero += 1
                numero_os = f"{prefixo}{proximo_numero:04d}"
                tentativas += 1
            
            return numero_os
            
        except Exception as e:
            # Fallback EXTREMO: gera número timestamp-based
            print(f"⚠️ ERRO CRÍTICO ao gerar número de OS: {e}")
            from datetime import datetime
            timestamp = datetime.now().strftime("%H%M%S")
            return f"{prefixo}{timestamp[-4:]}"

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
    unit = Column(String(20), nullable=False, default='un')
    unit_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    technician_notes = Column(Text, nullable=True)
    
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
    product_name = Column(String(200), nullable=True)
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
    status = Column(String(20), nullable=False, default='pending')
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


class ServiceOrderEquipment(Base):
    """
    Tabela de equipamentos vinculados à ordem de serviço.
    """
    __tablename__ = "service_order_equipments"
    __table_args__ = {"schema": "core"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    service_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.service_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    equipment_name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    accessories = Column(Text, nullable=True)
    defect_reported = Column(Text, nullable=True)
    technical_diagnosis = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, server_default=text("now()"))

    service_order = relationship("ServiceOrder", back_populates="equipments")

    def __repr__(self):
        return f"<ServiceOrderEquipment(id={self.id}, equipment_name={self.equipment_name})>"

"""
Model SQLAlchemy para tabela core.proposals (Propostas/Orçamentos)
Propostas aprovadas podem ser convertidas em Ordens de Serviço
"""
from sqlalchemy import Column, String, Text, Numeric, Date, TIMESTAMP, ForeignKey, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Proposal(Base):
    """
    Tabela de propostas comerciais/orçamentos
    Schema: core
    Status: rascunho, enviada, aprovada, rejeitada, cancelada
    """
    __tablename__ = "proposals"
    __table_args__ = {"schema": "core"}

    # Identificação
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    number = Column(String(50), unique=True, nullable=False, index=True)  # PROP2025001
    
    # Dados do Cliente
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    customer_contact = Column(String(200))  # Contato do cliente
    
    # Dados da Proposta
    title = Column(String(200), nullable=False)
    description = Column(Text)
    observations = Column(Text)  # Observações internas
    
    # Valores
    service_amount = Column(Numeric(12, 2), server_default=text("0"))  # Valor de serviços
    parts_amount = Column(Numeric(12, 2), server_default=text("0"))  # Valor de materiais/peças
    discount_amount = Column(Numeric(12, 2), server_default=text("0"))  # Desconto
    total_amount = Column(Numeric(12, 2), nullable=False, server_default=text("0"))  # Total final
    
    # Datas
    issue_date = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))  # Data de emissão
    validity_date = Column(Date)  # Data de validade da proposta
    approval_date = Column(Date)  # Data de aprovação
    
    # Status e Workflow
    status = Column(
        String(20),
        nullable=False,
        server_default=text("'rascunho'"),
        index=True
    )  # rascunho, enviada, aprovada, rejeitada, cancelada
    
    # Condições
    payment_condition = Column(String(50))  # a_vista, parcelado, etc
    delivery_days = Column(String(50))  # Prazo de entrega
    warranty_days = Column(String(50))  # Garantia
    
    # Responsável
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="SET NULL"),
        index=True
    )  # Usuário que criou a proposta
    approved_by = Column(String(200))  # Nome de quem aprovou (cliente)
    
    # Controle
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, onupdate=text("now()"))
    deleted_at = Column(TIMESTAMP, nullable=True, index=True)
    deleted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="SET NULL")
    )
    
    # Compartilhamento Público (Share Link)
    share_token = Column(String(64), unique=True, nullable=True, index=True)  # Token único para compartilhamento
    share_enabled = Column(Boolean, server_default=text("false"))  # Se o compartilhamento está ativo
    share_expires_at = Column(TIMESTAMP, nullable=True)  # Data de expiração do link (opcional)
    share_created_at = Column(TIMESTAMP, nullable=True)  # Quando o link foi gerado
    
    # Relacionamentos
    customer = relationship("Customer", foreign_keys=[customer_id], lazy="joined")
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    service_orders = relationship(
        "ServiceOrder",
        back_populates="proposal",
        foreign_keys="ServiceOrder.proposta_id",
        lazy="select"
    )  # Uma proposta pode gerar uma ou mais OS

    def __repr__(self):
        return f"<Proposal(id={self.id}, number={self.number}, status={self.status}, total={self.total_amount})>"


class ProposalItem(Base):
    """
    Itens de serviço da proposta
    Schema: core
    """
    __tablename__ = "proposal_items"
    __table_args__ = {"schema": "core"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    description = Column(Text, nullable=False)
    service_type = Column(String(20), nullable=False)  # hora, dia, fechado
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"))

    # Relacionamento
    proposal = relationship("Proposal", foreign_keys=[proposal_id], lazy="select")


class ProposalProduct(Base):
    """
    Produtos/materiais da proposta
    Schema: core
    """
    __tablename__ = "proposal_products"
    __table_args__ = {"schema": "core"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.products.id", ondelete="RESTRICT"),
        nullable=True
    )
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"))

    # Relacionamentos
    proposal = relationship("Proposal", foreign_keys=[proposal_id], lazy="select")
    product = relationship("Product", foreign_keys=[product_id], lazy="select")

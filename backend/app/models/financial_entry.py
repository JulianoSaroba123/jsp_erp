"""
Model SQLAlchemy para tabela core.financial_entries
Lançamentos financeiros com integração automática de pedidos
"""
from sqlalchemy import Column, Text, Numeric, VARCHAR, ForeignKey, Boolean, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.database import Base


class FinancialEntry(Base):
    """
    Tabela de lançamentos financeiros (receitas/despesas).
    
    Schema: core
    
    Atributos:
        id: UUID primary key
        order_id: UUID opcional (FK para core.orders, NULL se lançamento manual)
        user_id: UUID obrigatório (FK para core.users)
        kind: 'revenue' ou 'expense'
        status: 'pending', 'paid', 'canceled'
        amount: Valor (>= 0)
        description: Descrição textual
        occurred_at: Data de ocorrência do lançamento
        created_at: Data de criação do registro
        updated_at: Data de última atualização
    
    Constraints:
        - UNIQUE(order_id): Um lançamento automático por pedido
        - CHECK kind IN ('revenue', 'expense')
        - CHECK status IN ('pending', 'paid', 'canceled')
        - CHECK amount >= 0
    """
    __tablename__ = "financial_entries"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('revenue', 'expense')",
            name="check_financial_kind"
        ),
        CheckConstraint(
            "status IN ('pending', 'paid', 'canceled')",
            name="check_financial_status"
        ),
        CheckConstraint(
            "amount >= 0",
            name="check_financial_amount_positive"
        ),
        {"schema": "core"}
    )

    # Colunas
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.orders.id", ondelete="SET NULL"),
        nullable=True,  # Pode ser NULL (lançamento manual)
        unique=True,  # UNIQUE: um lançamento por pedido
        index=True
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    kind = Column(
        VARCHAR(20),
        nullable=False,
        comment="Tipo: revenue (receita) ou expense (despesa)"
    )
    
    status = Column(
        VARCHAR(20),
        nullable=False,
        server_default=text("'pending'"),
        index=True,
        comment="Status: pending, paid, canceled"
    )
    
    amount = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Valor do lançamento (>= 0)"
    )
    
    description = Column(
        Text,
        nullable=False,
        comment="Descrição do lançamento"
    )

    # Campos profissionais Phase 1
    category = Column(VARCHAR(100), nullable=True)
    subcategory = Column(VARCHAR(100), nullable=True)
    due_date = Column(TIMESTAMP(timezone=True), nullable=True)
    payment_date = Column(TIMESTAMP(timezone=True), nullable=True)
    document_number = Column(VARCHAR(50), nullable=True)
    document_type = Column(VARCHAR(50), nullable=True)
    payment_method = Column(VARCHAR(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Relacionamentos opcionais
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.customers.id", ondelete="SET NULL"),
        nullable=True
    )
    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.suppliers.id", ondelete="SET NULL"),
        nullable=True
    )
    service_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.service_orders.id", ondelete="SET NULL"),
        nullable=True
    )

    # Cálculos financeiros
    original_amount = Column(Numeric(12, 2), nullable=True)
    interest = Column(Numeric(12, 2), nullable=True)
    discount = Column(Numeric(12, 2), nullable=True)
    penalty = Column(Numeric(12, 2), nullable=True)

    # Parcelamento e recorrência
    installment_info = Column(VARCHAR(100), nullable=True)
    is_recurring = Column(Boolean, nullable=True, server_default=text("false"))
    recurrence_frequency = Column(VARCHAR(20), nullable=True)

    # Origem
    origin = Column(VARCHAR(50), nullable=True)
    
    occurred_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
        comment="Data de ocorrência do lançamento"
    )
    
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True
    )
    
    # Soft Delete
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    deleted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relacionamentos
    user = relationship("User", foreign_keys=[user_id], back_populates="financial_entries", lazy="select")
    order = relationship("Order", back_populates="financial_entry", lazy="select")

    def __repr__(self):
        return (
            f"<FinancialEntry(id={self.id}, kind={self.kind}, "
            f"status={self.status}, amount={self.amount})>"
        )

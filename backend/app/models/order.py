"""
Model SQLAlchemy para tabela core.orders
"""
from sqlalchemy import Column, Text, Numeric, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Order(Base):
    """
    Tabela de pedidos/ordens.
    Schema: core
    """
    __tablename__ = "orders"
    __table_args__ = {"schema": "core"}

    # Colunas
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")  # UUID gerado no banco
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="CASCADE"),  # Sempre com schema
        nullable=False,
        index=True
    )
    description = Column(Text, nullable=False)
    total = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    created_at = Column(TIMESTAMP, server_default=text("now()"))

    # Relacionamentos
    user = relationship("User", back_populates="orders", lazy="select")
    financial_entry = relationship(
        "FinancialEntry",
        back_populates="order",
        uselist=False,  # One-to-One (um pedido -> um lançamento)
        lazy="select"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total={self.total})>"


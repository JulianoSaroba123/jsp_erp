"""
Model SQLAlchemy para tabela core.users
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    Tabela de usuários do sistema.
    Schema: core
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "core"}

    # Colunas
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")  # UUID gerado no banco
    )
    name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)  # NUNCA expor em schemas
    role = Column(String(50), nullable=False)  # ex: admin, user
    is_active = Column(Boolean, default=True, server_default=text("true"))
    created_at = Column(TIMESTAMP, server_default=text("now()"))

    # Relacionamentos
    orders = relationship("Order", back_populates="user", lazy="select")
    financial_entries = relationship("FinancialEntry", back_populates="user", lazy="select")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

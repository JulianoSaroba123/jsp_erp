"""
Model SQLAlchemy para tabela core.permissions
"""
from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.role import role_permissions


class Permission(Base):
    """
    Tabela de permissões (orders:read, orders:delete, etc.)
    Schema: core
    
    Formato: resource:action
    - resource: orders, users, financial, etc.
    - action: read, create, update, delete, etc.
    
    Relacionamentos:
    - roles (N:N via role_permissions)
    """
    __tablename__ = "permissions"
    __table_args__ = {"schema": "core"}

    # Colunas
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("now()"))

    # Relacionamentos
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="select"
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, resource='{self.resource}', action='{self.action}')>"
    
    @property
    def full_name(self) -> str:
        """Retorna permissão no formato resource:action"""
        return f"{self.resource}:{self.action}"

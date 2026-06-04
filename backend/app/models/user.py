"""
SQLAlchemy model for core.users.
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.role import user_roles


class User(Base):
    """
    System users table.
    Schema: core
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "core"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, server_default=text("true"))
    created_at = Column(TIMESTAMP, server_default=text("now()"))

    orders = relationship(
        "Order",
        back_populates="user",
        lazy="select",
        foreign_keys="[Order.user_id]",
    )
    financial_entries = relationship(
        "FinancialEntry",
        back_populates="user",
        lazy="select",
        foreign_keys="[FinancialEntry.user_id]",
    )

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="select",
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    def has_permission(self, resource: str, action: str) -> bool:
        """
        Return True when any assigned RBAC role grants the requested permission.
        """
        for role in self.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        return False

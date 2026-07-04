"""
SQLAlchemy model for core.roles and RBAC association tables.
"""
from sqlalchemy import Column, String, TIMESTAMP, text, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("core.users.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("core.roles.id"), primary_key=True),
    Column("assigned_at", TIMESTAMP, server_default=text("now()")),
    schema="core",
)


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("core.roles.id"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("core.permissions.id"), primary_key=True),
    Column("assigned_at", TIMESTAMP, server_default=text("now()")),
    schema="core",
)


class Role(Base):
    """
    Role/profile table (admin, user, technician, etc.).
    Schema: core
    """
    __tablename__ = "roles"
    __table_args__ = {"schema": "core"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("now()"))

    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="select",
    )

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="select",
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

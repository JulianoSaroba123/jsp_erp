"""
Audit Log Model

Modelo para rastreamento de todas operações críticas do sistema.
Registra quem fez, quando, o quê e o estado antes/depois.

ETAPA 6 - Features Enterprise
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    """
    Modelo de Audit Log.
    
    Registra todas as operações CREATE, UPDATE, DELETE no sistema.
    Permite rastreabilidade completa e compliance.
    
    Attributes:
        id: UUID único do log
        user_id: ID do usuário que executou a ação
        action: Tipo de operação (create/update/delete)
        entity_type: Tipo de entidade afetada (order/financial_entry/user)
        entity_id: ID da entidade afetada
        before: Estado anterior (JSON) - NULL em create
        after: Estado atual (JSON) - NULL em delete
        request_id: X-Request-ID do middleware para correlação
        created_at: Timestamp da operação
        
    Relationships:
        user: Usuário que executou a ação
        
    Indexes:
        - user_id: Consultas por usuário
        - (entity_type, entity_id): Histórico de uma entidade
        - created_at DESC: Eventos recentes
        - request_id: Rastreamento de requisição
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "action IN ('create', 'update', 'delete')",
            name='check_audit_action'
        ),
        CheckConstraint(
            "entity_type IN ('order', 'financial_entry', 'user')",
            name='check_audit_entity_type'
        ),
        {'schema': 'core'}
    )
    
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="UUID único do log de auditoria"
    )
    
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('core.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Usuário que executou a ação"
    )
    
    action = Column(
        String(20),
        nullable=False,
        comment="Tipo de operação: create, update, delete"
    )
    
    entity_type = Column(
        String(50),
        nullable=False,
        comment="Tipo de entidade: order, financial_entry, user"
    )
    
    entity_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="ID da entidade afetada"
    )
    
    before = Column(
        JSONB,
        nullable=True,
        comment="Estado anterior da entidade (NULL em create)"
    )
    
    after = Column(
        JSONB,
        nullable=True,
        comment="Estado atual da entidade (NULL em delete)"
    )
    
    request_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="X-Request-ID do middleware para correlação"
    )
    
    created_at = Column(
        TIMESTAMP,
        server_default=text("now()"),
        nullable=False,
        index=True,
        comment="Timestamp da operação"
    )
    
    # Relationships
    user = relationship("User", backref="audit_logs")
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog("
            f"id='{self.id}', "
            f"action='{self.action}', "
            f"entity='{self.entity_type}:{self.entity_id}', "
            f"user_id='{self.user_id}'"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            dict: Audit log data
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "before": self.before,
            "after": self.after,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

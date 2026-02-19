"""
Audit Log Service

Serviço para registro e consulta de audit logs.
Fornece rastreabilidade completa de operações no sistema.

ETAPA 6 - Features Enterprise
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit_log_schema import AuditLogCreate, AuditLogResponse


class AuditLogService:
    """
    Serviço de Audit Log.
    
    Responsável por:
    - Registrar operações (create/update/delete)
    - Consultar histórico de auditoria
    - Rastrear mudanças em entidades
    """
    
    @staticmethod
    def log_action(
        db: Session,
        user_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID,
        request_id: str,
        before: Optional[dict[str, Any]] = None,
        after: Optional[dict[str, Any]] = None
    ) -> AuditLog:
        """
        Registra uma ação no audit log.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário que executou a ação
            action: Tipo de operação (create/update/delete)
            entity_type: Tipo de entidade (order/financial_entry/user)
            entity_id: ID da entidade afetada
            request_id: X-Request-ID da requisição
            before: Estado anterior (opcional, NULL em create)
            after: Estado atual (opcional, NULL em delete)
            
        Returns:
            AuditLog: Log criado
            
        Examples:
            >>> # Registrar criação
            >>> log_action(
            ...     db, user_id, "create", "order", order_id, request_id,
            ...     before=None, after={"description": "New", "total": 100}
            ... )
            
            >>> # Registrar update
            >>> log_action(
            ...     db, user_id, "update", "order", order_id, request_id,
            ...     before={"total": 100}, after={"total": 150}
            ... )
            
            >>> # Registrar delete
            >>> log_action(
            ...     db, user_id, "delete", "order", order_id, request_id,
            ...     before={"description": "Old", "total": 100}, after=None
            ... )
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            request_id=request_id
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    def get_logs(
        db: Session,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[AuditLog], int]:
        """
        Consulta audit logs com filtros.
        
        Args:
            db: Sessão do banco de dados
            user_id: Filtrar por usuário (opcional)
            action: Filtrar por ação (opcional)
            entity_type: Filtrar por tipo de entidade (opcional)
            entity_id: Filtrar por ID da entidade (opcional)
            date_from: Data início (opcional)
            date_to: Data fim (opcional)
            skip: Offset para paginação
            limit: Limite de resultados
            
        Returns:
            tuple[list[AuditLog], int]: (logs, total_count)
        """
        query = db.query(AuditLog)
        
        # Aplicar filtros
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        
        if action:
            conditions.append(AuditLog.action == action)
        
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        
        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)
        
        if date_from:
            conditions.append(AuditLog.created_at >= date_from)
        
        if date_to:
            conditions.append(AuditLog.created_at <= date_to)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Total count
        total = query.count()
        
        # Ordenar por mais recente e paginar
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        
        return logs, total
    
    @staticmethod
    def get_entity_history(
        db: Session,
        entity_type: str,
        entity_id: UUID
    ) -> list[AuditLog]:
        """
        Obtém histórico completo de uma entidade.
        
        Args:
            db: Sessão do banco de dados
            entity_type: Tipo de entidade
            entity_id: ID da entidade
            
        Returns:
            list[AuditLog]: Histórico ordenado por data
        """
        return (
            db.query(AuditLog)
            .filter(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id
                )
            )
            .order_by(AuditLog.created_at)
            .all()
        )
    
    @staticmethod
    def get_user_actions(
        db: Session,
        user_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> list[AuditLog]:
        """
        Obtém todas ações de um usuário em um período.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            date_from: Data início (opcional)
            date_to: Data fim (opcional)
            
        Returns:
            list[AuditLog]: Ações do usuário
        """
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
        
        if date_from:
            query = query.filter(AuditLog.created_at >= date_from)
        
        if date_to:
            query = query.filter(AuditLog.created_at <= date_to)
        
        return query.order_by(desc(AuditLog.created_at)).all()

"""
Audit Log Routes

Endpoints para consulta de audit logs.
Apenas admins podem acessar.

ETAPA 6 - Features Enterprise
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.audit_log_schema import AuditLogListResponse, AuditLogResponse
from app.security.deps import get_current_user, require_admin, get_db
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)]
)
def get_audit_logs(
    user_id: Optional[UUID] = Query(None, description="Filtrar por usuário"),
    action: Optional[str] = Query(None, description="Filtrar por ação (create/update/delete)"),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidade"),
    entity_id: Optional[UUID] = Query(None, description="Filtrar por ID da entidade"),
    date_from: Optional[datetime] = Query(None, description="Data início (YYYY-MM-DD ou ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Data fim (YYYY-MM-DD ou ISO 8601)"),
    page: int = Query(1, ge=1, description="Número da página (começa em 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista audit logs com filtros opcionais.
    
    **Autenticação obrigatória: apenas ADMIN**
    
    Permite rastrear:
    - Todas ações de um usuário específico
    - Histórico de uma entidade (order, financial_entry, user)
    - Operações em um período de tempo
    - Tipos específicos de ação (create/update/delete)
    
    Retorna resultados paginados ordenados por mais recente.
    
    Exemplos de uso:
    - `/audit-logs` → Últimos 20 logs
    - `/audit-logs?user_id={uuid}` → Ações de um usuário
    - `/audit-logs?entity_type=order&entity_id={uuid}` → Histórico de um pedido
    - `/audit-logs?action=delete&date_from=2026-02-01` → Deleções desde fevereiro
    """
    skip = (page - 1) * page_size
    
    logs, total = AuditLogService.get_logs(
        db=db,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=page_size
    )
    
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=list[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)]
)
def get_entity_history(
    entity_type: str,
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém histórico completo de uma entidade.
    
    **Autenticação obrigatória: apenas ADMIN**
    
    Retorna todos os logs relacionados a uma entidade específica,
    ordenados cronologicamente (do mais antigo ao mais recente).
    
    Útil para:
    - Ver todas mudanças em um pedido
    - Rastrear evolução de um lançamento financeiro
    - Auditar alterações em usuários

    Args:
        entity_type: Tipo da entidade (order, financial_entry, user)
        entity_id: UUID da entidade
    
    Returns:
        Lista de logs ordenada cronologicamente
    """
    logs = AuditLogService.get_entity_history(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get(
    "/user/{user_id}",
    response_model=list[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)]
)
def get_user_actions(
    user_id: UUID,
    date_from: Optional[datetime] = Query(None, description="Data início"),
    date_to: Optional[datetime] = Query(None, description="Data fim"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém todas ações de um usuário em um período.
    
    **Autenticação obrigatória: apenas ADMIN**
    
    Retorna todos os logs de um usuário específico,
    ordenados do mais recente ao mais antigo.
    
    Útil para:
    - Auditoria de ações de um usuário específico
    - Investigação de incidentes
    - Relatórios de compliance
    
    Args:
        user_id: UUID do usuário
        date_from: Data início do período (opcional)
        date_to: Data fim do período (opcional)
    
    Returns:
        Lista de ações do usuário
    """
    logs = AuditLogService.get_user_actions(
        db=db,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]

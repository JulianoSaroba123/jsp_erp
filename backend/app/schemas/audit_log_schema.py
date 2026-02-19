"""
Audit Log Schemas

Schemas Pydantic para validação de audit logs.

ETAPA 6 - Features Enterprise
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    """Base schema para audit log."""
    action: str = Field(..., description="Tipo de operação: create, update, delete")
    entity_type: str = Field(..., description="Tipo de entidade: order, financial_entry, user")
    entity_id: UUID = Field(..., description="ID da entidade afetada")


class AuditLogCreate(AuditLogBase):
    """Schema para criação de audit log (interno)."""
    user_id: UUID
    before: Optional[dict[str, Any]] = Field(None, description="Estado anterior (NULL em create)")
    after: Optional[dict[str, Any]] = Field(None, description="Estado atual (NULL em delete)")
    request_id: str = Field(..., description="X-Request-ID da requisição")


class AuditLogResponse(AuditLogBase):
    """Schema para resposta de audit log."""
    id: UUID
    user_id: UUID
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None
    request_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "action": "update",
                "entity_type": "order",
                "entity_id": "123e4567-e89b-12d3-a456-426614174002",
                "before": {
                    "description": "Old Order",
                    "total": 100.00
                },
                "after": {
                    "description": "Updated Order",
                    "total": 150.00
                },
                "request_id": "req-abc-123",
                "created_at": "2026-02-18T10:00:00"
            }
        }


class AuditLogFilter(BaseModel):
    """Schema para filtros de consulta de audit logs."""
    user_id: Optional[UUID] = Field(None, description="Filtrar por usuário")
    action: Optional[str] = Field(None, description="Filtrar por ação (create/update/delete)")
    entity_type: Optional[str] = Field(None, description="Filtrar por tipo de entidade")
    entity_id: Optional[UUID] = Field(None, description="Filtrar por ID da entidade")
    date_from: Optional[datetime] = Field(None, description="Data início")
    date_to: Optional[datetime] = Field(None, description="Data fim")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "action": "delete",
                "entity_type": "order",
                "date_from": "2026-02-01T00:00:00",
                "date_to": "2026-02-28T23:59:59"
            }
        }


class AuditLogListResponse(BaseModel):
    """Schema para lista paginada de audit logs."""
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "action": "create",
                        "entity_type": "order",
                        "entity_id": "123e4567-e89b-12d3-a456-426614174002",
                        "before": None,
                        "after": {"description": "New Order", "total": 100.00},
                        "request_id": "req-abc-123",
                        "created_at": "2026-02-18T10:00:00"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20
            }
        }

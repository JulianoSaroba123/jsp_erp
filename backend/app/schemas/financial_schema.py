"""
Schemas Pydantic para FinancialEntry.
Separação: Request (entrada) e Response (saída).
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional


class FinancialEntryCreate(BaseModel):
    """
    Schema para criação de lançamento manual.
    
    user_id NÃO é aceito no body - vem do token JWT.
    order_id NÃO é aceito (lançamento manual).
    """
    kind: str = Field(..., description="Tipo: 'revenue' ou 'expense'")
    amount: Decimal = Field(..., ge=0, description="Valor (>= 0)")
    description: str = Field(..., min_length=1, max_length=500, description="Descrição do lançamento")
    occurred_at: Optional[datetime] = Field(None, description="Data de ocorrência (default: now)")
    
    model_config = {"json_schema_extra": {
        "example": {
            "kind": "expense",
            "amount": 150.50,
            "description": "Pagamento de fornecedor XYZ",
            "occurred_at": "2026-02-15T10:30:00"
        }
    }}


class FinancialEntryResponse(BaseModel):
    """Schema de saída de lançamento financeiro."""
    id: UUID
    order_id: Optional[UUID]
    user_id: UUID
    kind: str
    status: str
    amount: float  # Serializado como number (não string) para compatibilidade frontend
    description: str
    occurred_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class FinancialEntryUpdateStatus(BaseModel):
    """Schema para atualização de status."""
    status: str = Field(..., description="Novo status: 'pending', 'paid', 'canceled'")
    
    model_config = {"json_schema_extra": {
        "example": {
            "status": "paid"
        }
    }}


class FinancialEntryListResponse(BaseModel):
    """Schema de resposta paginada."""
    items: list[FinancialEntryResponse]
    page: int
    page_size: int
    total: int

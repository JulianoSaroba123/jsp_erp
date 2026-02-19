"""
Schemas Pydantic para Order.
Separação: Create (entrada) e Out (saída).
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class OrderCreate(BaseModel):
    """
    Schema para criação de pedido (entrada).
    
    **DEPRECATED para uso direto em rotas protegidas.**
    Use OrderCreateRequest em rotas autenticadas (user_id vem do token).
    """
    user_id: UUID = Field(..., description="UUID do usuário")
    description: str = Field(..., min_length=1, max_length=500, description="Descrição do pedido")
    total: Decimal = Field(..., ge=0, description="Valor total (>= 0)")


class OrderCreateRequest(BaseModel):
    """
    Schema para criação de pedido em rota autenticada.
    
    user_id NÃO é aceito no body - é obtido do token JWT.
    Isso garante que usuários só possam criar pedidos para si mesmos.
    """
    description: str = Field(..., min_length=1, max_length=500, description="Descrição do pedido")
    total: Decimal = Field(..., ge=0, description="Valor total (>= 0)")
    
    model_config = {"json_schema_extra": {
        "example": {
            "description": "Pedido de teste",
            "total": 150.50
        }
    }}


class OrderOut(BaseModel):
    """Schema de saída de pedido (response)."""
    id: UUID
    user_id: UUID
    description: str
    total: float  # Serializado como number (não string) para compatibilidade frontend
    created_at: datetime

    class Config:
        from_attributes = True  # Permite conversão de ORM model


class OrderUpdate(BaseModel):
    """
    Schema para atualização parcial de pedido (PATCH).
    
    Todos os campos são opcionais.
    - description: Nova descrição do pedido
    - total: Novo valor total (sincroniza com lançamento financeiro)
    
    Regras:
    - user_id é IMUTÁVEL (multi-tenant protegido)
    - total não pode ser alterado se financeiro está "paid"
    - total = 0 cancela financeiro (se pending)
    - total > 0 reabre financeiro cancelado ou cria novo
    """
    description: str | None = Field(None, min_length=3, max_length=500)
    total: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    
    model_config = {"json_schema_extra": {
        "example": {
            "description": "Pedido atualizado",
            "total": 150.50
        }
    }}

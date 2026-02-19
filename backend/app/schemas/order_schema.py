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
    total: float  # Changed from Decimal to float for JSON serialization
    created_at: datetime

    class Config:
        from_attributes = True  # Permite conversão de ORM model

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
    
    # Campos profissionais Phase 1
    category: Optional[str] = Field(None, max_length=100, description="Categoria (ex: Vendas, Serviços, Fornecedores)")
    subcategory: Optional[str] = Field(None, max_length=100, description="Subcategoria (ex: Produtos, Manutenção)")
    due_date: Optional[datetime] = Field(None, description="Data de vencimento")
    payment_date: Optional[datetime] = Field(None, description="Data de pagamento efetivo")
    document_number: Optional[str] = Field(None, max_length=50, description="Número do documento (NF, recibo, etc)")
    document_type: Optional[str] = Field(None, max_length=50, description="Tipo do documento (NF-e, boleto, recibo)")
    payment_method: Optional[str] = Field(None, max_length=50, description="Forma de pagamento (pix, dinheiro, cartão)")
    notes: Optional[str] = Field(None, description="Observações adicionais")
    
    # Relacionamentos
    customer_id: Optional[UUID] = Field(None, description="ID do cliente (se for receita)")
    supplier_id: Optional[UUID] = Field(None, description="ID do fornecedor (se for despesa)")
    service_order_id: Optional[UUID] = Field(None, description="ID da ordem de serviço relacionada")
    
    # Cálculos financeiros
    original_amount: Optional[Decimal] = Field(None, ge=0, description="Valor original antes de juros/descontos")
    interest: Optional[Decimal] = Field(None, ge=0, description="Juros aplicados")
    discount: Optional[Decimal] = Field(None, ge=0, description="Desconto concedido")
    penalty: Optional[Decimal] = Field(None, ge=0, description="Multa por atraso")
    
    # Parcelamento e recorrência
    installment_info: Optional[str] = Field(None, max_length=100, description="Info de parcelas (ex: 3/12)")
    is_recurring: Optional[bool] = Field(False, description="É um lançamento recorrente?")
    recurrence_frequency: Optional[str] = Field(None, max_length=20, description="Frequência (mensal, anual)")
    
    # Origem
    origin: Optional[str] = Field(None, max_length=50, description="Origem do lançamento (manual, pedido, importação)")
    
    model_config = {"json_schema_extra": {
        "example": {
            "kind": "expense",
            "amount": 150.50,
            "description": "Pagamento de fornecedor XYZ",
            "occurred_at": "2026-02-15T10:30:00",
            "category": "Fornecedores",
            "subcategory": "Eletrônicos",
            "due_date": "2026-02-20T00:00:00",
            "payment_method": "pix",
            "document_number": "NF-12345",
            "document_type": "NF-e"
        }
    }}


class FinancialEntryResponse(BaseModel):
    """Schema de saída de lançamento financeiro."""
    id: UUID
    order_id: Optional[UUID]
    user_id: UUID
    kind: str
    status: str
    amount: float  # Changed from Decimal to float for JSON serialization
    description: str
    occurred_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Campos profissionais Phase 1
    category: Optional[str] = None
    subcategory: Optional[str] = None
    due_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    document_number: Optional[str] = None
    document_type: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    
    # Relacionamentos
    customer_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    service_order_id: Optional[UUID] = None
    
    # Cálculos financeiros
    original_amount: Optional[float] = None
    interest: Optional[float] = None
    discount: Optional[float] = None
    penalty: Optional[float] = None
    
    # Parcelamento e recorrência
    installment_info: Optional[str] = None
    is_recurring: Optional[bool] = False
    recurrence_frequency: Optional[str] = None
    
    # Origem
    origin: Optional[str] = None

    model_config = {"from_attributes": True}


class FinancialEntryUpdateStatus(BaseModel):
    """Schema para atualização de status."""
    status: str = Field(..., description="Novo status: 'pending', 'paid', 'canceled'")
    payment_date: Optional[datetime] = Field(None, description="Data de pagamento (usado quando status='paid')")
    
    model_config = {"json_schema_extra": {
        "example": {
            "status": "paid",
            "payment_date": "2026-03-16T14:30:00"
        }
    }}


class FinancialEntryUpdate(BaseModel):
    """Schema para atualização completa de lançamento."""
    kind: Optional[str] = Field(None, description="Tipo: 'revenue' ou 'expense'")
    amount: Optional[Decimal] = Field(None, ge=0, description="Valor (>= 0)")
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    occurred_at: Optional[datetime] = None
    status: Optional[str] = None
    
    # Campos profissionais
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    due_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    document_number: Optional[str] = Field(None, max_length=50)
    document_type: Optional[str] = Field(None, max_length=50)
    payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    
    # Relacionamentos
    customer_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    service_order_id: Optional[UUID] = None
    
    # Cálculos financeiros
    original_amount: Optional[Decimal] = Field(None, ge=0)
    interest: Optional[Decimal] = Field(None, ge=0)
    discount: Optional[Decimal] = Field(None, ge=0)
    penalty: Optional[Decimal] = Field(None, ge=0)
    
    # Parcelamento e recorrência
    installment_info: Optional[str] = Field(None, max_length=100)
    is_recurring: Optional[bool] = None
    recurrence_frequency: Optional[str] = Field(None, max_length=20)
    
    # Origem
    origin: Optional[str] = Field(None, max_length=50)
    
    model_config = {"json_schema_extra": {
        "example": {
            "status": "paid",
            "payment_date": "2026-03-16T14:30:00",
            "payment_method": "pix",
            "notes": "Pagamento confirmado via PIX"
        }
    }}


class FinancialEntryListResponse(BaseModel):
    """Schema de resposta paginada."""
    items: list[FinancialEntryResponse]
    page: int
    page_size: int
    total: int

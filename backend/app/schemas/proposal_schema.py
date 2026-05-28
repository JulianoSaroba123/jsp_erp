"""
Schemas Pydantic para Proposals (Propostas Comerciais / Orçamentos).
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date
from typing import Optional, Literal, List
from decimal import Decimal


# ==================== ProposalItem Schemas ====================

class ProposalItemCreate(BaseModel):
    """Schema para criação de item de serviço da proposta."""
    description: str = Field(..., min_length=1, description="Descrição do serviço")
    service_type: Literal['hora', 'dia', 'fechado'] = Field('hora', description="Tipo: hora, dia ou fechado")
    quantity: Decimal = Field(1.00, ge=0, description="Quantidade")
    unit_price: Decimal = Field(0.00, ge=0, description="Valor unitário")
    total_price: Decimal = Field(0.00, ge=0, description="Valor total")


class ProposalItemOut(BaseModel):
    """Schema de saída de item de serviço."""
    id: UUID
    proposal_id: UUID
    description: str
    service_type: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== ProposalProduct Schemas ====================

class ProposalProductCreate(BaseModel):
    """Schema para criação de produto da proposta."""
    product_id: Optional[UUID] = Field(None, description="ID do produto cadastrado (opcional)")
    description: str = Field(..., min_length=1, description="Descrição do produto/material")
    quantity: Decimal = Field(1.000, ge=0, description="Quantidade")
    unit_price: Decimal = Field(0.00, ge=0, description="Valor unitário")
    total_price: Decimal = Field(0.00, ge=0, description="Valor total")


class ProposalProductOut(BaseModel):
    """Schema de saída de produto."""
    id: UUID
    proposal_id: UUID
    product_id: Optional[UUID]
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== Proposal Schemas ====================

class ProposalCreate(BaseModel):
    """Schema para criação de proposta comercial."""
    # O número será gerado automaticamente (PROP2025001, PROP2025002...)
    customer_id: UUID = Field(..., description="ID do cliente")
    customer_contact: Optional[str] = Field(None, max_length=200, description="Contato do cliente")
    
    # Dados da proposta
    title: str = Field(..., min_length=1, max_length=200, description="Título da proposta")
    description: Optional[str] = Field(None, description="Descrição detalhada")
    observations: Optional[str] = Field(None, description="Observações internas")
    
    # Valores
    service_amount: Decimal = Field(0.00, ge=0, description="Valor dos serviços")
    parts_amount: Decimal = Field(0.00, ge=0, description="Valor de materiais/peças")
    discount_amount: Decimal = Field(0.00, ge=0, description="Desconto")
    total_amount: Decimal = Field(0.00, ge=0, description="Valor total")
    
    # Datas
    issue_date: Optional[date] = Field(None, description="Data de emissão (padrão: hoje)")
    validity_date: Optional[date] = Field(None, description="Data de validade")
    approval_date: Optional[date] = Field(None, description="Data de aprovação")
    
    # Status
    status: Literal['rascunho', 'enviada', 'aprovada', 'rejeitada', 'cancelada'] = Field(
        'rascunho',
        description="Status da proposta"
    )
    
    # Condições
    payment_condition: Optional[str] = Field(None, max_length=50, description="Condição de pagamento")
    delivery_days: Optional[str] = Field(None, max_length=50, description="Prazo de entrega")
    warranty_days: Optional[str] = Field(None, max_length=50, description="Garantia")
    
    # Aprovação
    approved_by: Optional[str] = Field(None, max_length=200, description="Nome de quem aprovou")
    
    # Itens relacionados (opcionais no create)
    items: Optional[List[ProposalItemCreate]] = Field([], description="Itens de serviço")
    products: Optional[List[ProposalProductCreate]] = Field([], description="Produtos/materiais")

    model_config = {"json_schema_extra": {
        "example": {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Proposta para instalação de rede corporativa",
            "description": "Instalação completa de cabeamento Cat6, switches e access points",
            "service_amount": 5000.00,
            "parts_amount": 3000.00,
            "discount_amount": 500.00,
            "total_amount": 7500.00,
            "status": "enviada",
            "payment_condition": "50% entrada + 50% na conclusão",
            "delivery_days": "15 dias úteis",
            "warranty_days": "12 meses"
        }
    }}


class ProposalUpdate(BaseModel):
    """Schema para atualização parcial (PATCH)."""
    customer_id: Optional[UUID] = None
    customer_contact: Optional[str] = Field(None, max_length=200)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    observations: Optional[str] = None
    service_amount: Optional[Decimal] = Field(None, ge=0)
    parts_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    issue_date: Optional[date] = None
    validity_date: Optional[date] = None
    approval_date: Optional[date] = None
    status: Optional[Literal['rascunho', 'enviada', 'aprovada', 'rejeitada', 'cancelada']] = None
    payment_condition: Optional[str] = Field(None, max_length=50)
    delivery_days: Optional[str] = Field(None, max_length=50)
    warranty_days: Optional[str] = Field(None, max_length=50)
    approved_by: Optional[str] = Field(None, max_length=200)


class ProposalOut(BaseModel):
    """Schema de saída de proposta (response)."""
    id: UUID
    number: str
    customer_id: UUID
    customer_contact: Optional[str]
    title: str
    description: Optional[str]
    observations: Optional[str]
    service_amount: Decimal
    parts_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    issue_date: date
    validity_date: Optional[date]
    approval_date: Optional[date]
    status: str
    payment_condition: Optional[str]
    delivery_days: Optional[str]
    warranty_days: Optional[str]
    user_id: Optional[UUID]
    approved_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    
    # Relações opcionais
    items: Optional[List[ProposalItemOut]] = None
    products: Optional[List[ProposalProductOut]] = None
    
    model_config = {"from_attributes": True}


class ProposalSummary(BaseModel):
    """Schema resumido de proposta (para listagens)."""
    id: UUID
    number: str
    customer_id: UUID
    title: str
    status: str
    total_amount: Decimal
    issue_date: date
    validity_date: Optional[date]
    created_at: datetime
    
    model_config = {"from_attributes": True}


# ==================== Response Schemas ====================

class ProposalsResponse(BaseModel):
    """Response paginado de propostas."""
    items: List[ProposalSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class ConvertProposalToOSRequest(BaseModel):
    """Schema para conversão de proposta em ordem de serviço."""
    technician_id: Optional[UUID] = Field(None, description="ID do técnico responsável pela OS")
    expected_completion_date: Optional[date] = Field(None, description="Data prevista de conclusão")
    observations: Optional[str] = Field(None, description="Observações adicionais para a OS")
    
    model_config = {"json_schema_extra": {
        "example": {
            "technician_id": "123e4567-e89b-12d3-a456-426614174000",
            "expected_completion_date": "2025-12-31",
            "observations": "Cliente solicitou agendar para próxima semana"
        }
    }}


class ConvertProposalToOSResponse(BaseModel):
    """Response da conversão de proposta em OS."""
    success: bool
    message: str
    service_order_id: UUID
    service_order_number: str
    
    model_config = {"json_schema_extra": {
        "example": {
            "success": True,
            "message": "Proposta PROP2025001 convertida em OS OS2025015 com sucesso",
            "service_order_id": "789e4567-e89b-12d3-a456-426614174999",
            "service_order_number": "OS2025015"
        }
    }}


# ==================== Share Link Schemas ====================

class GenerateShareLinkRequest(BaseModel):
    """Schema para gerar link de compartilhamento."""
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Dias até expiração (None = sem expiração)")
    
    model_config = {"json_schema_extra": {
        "example": {
            "expires_in_days": 30
        }
    }}


class ShareLinkResponse(BaseModel):
    """Response com link de compartilhamento gerado."""
    share_token: str
    share_url: str
    share_enabled: bool
    share_expires_at: Optional[datetime]
    share_created_at: datetime
    
    model_config = {"json_schema_extra": {
        "example": {
            "share_token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "share_url": "http://localhost:8000/proposals/3f774ade-e01d-4827-88ef-8698d87e150b/share/pdf?token=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "share_enabled": True,
            "share_expires_at": "2026-04-12T10:30:00",
            "share_created_at": "2026-03-13T10:30:00"
        }
    }}


"""
Schemas Pydantic para Product.
Separação: Create (entrada), Update (PATCH), Out (saída).
"""

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional


class ProductCreate(BaseModel):
    """
    Schema para criação de produto.
    
    user_id vem do token JWT (não aceito no body).
    """
    code: Optional[str] = Field(None, max_length=50, description="Código interno do produto")
    name: str = Field(..., min_length=1, max_length=200, description="Nome do produto")
    category: Optional[str] = Field(None, max_length=80, description="Categoria")
    subcategoria: Optional[str] = Field(None, max_length=80, description="Subcategoria")
    unit: Optional[str] = Field(None, max_length=20, description="Unidade (un, m, kg, etc)")
    description: Optional[str] = Field(None, description="Descrição detalhada")
    
    # Identificação Estendida
    codigo_barras: Optional[str] = Field(None, max_length=50, description="Código de barras")
    marca: Optional[str] = Field(None, max_length=100, description="Marca do produto")
    modelo: Optional[str] = Field(None, max_length=100, description="Modelo do produto")
    
    # Características Físicas
    peso: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=3, description="Peso em kg")
    dimensoes: Optional[str] = Field(None, max_length=100, description="Dimensões (ex: 10x20x30 cm)")
    
    # Preços
    cost_price: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2, description="Preço de custo")
    sale_price: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2, description="Preço de venda")
    markup: Optional[Decimal] = Field(None, ge=0, le=1000, max_digits=5, decimal_places=2, description="Markup percentual")
    margem_lucro: Optional[Decimal] = Field(None, ge=-100, le=1000, max_digits=5, decimal_places=2, description="Margem de lucro")
    
    # Estoque
    stock_qty: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=3, description="Quantidade em estoque")
    stock_min: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=3, description="Estoque mínimo")
    estoque_maximo: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=3, description="Estoque máximo")
    controla_estoque: bool = Field(default=True, description="Controlar estoque")
    
    # Relacionamentos e Observações
    fornecedor_id: Optional[UUID] = Field(None, description="ID do fornecedor")
    observacoes: Optional[str] = Field(None, description="Observações gerais")
    
    # Status
    active: bool = Field(default=True, description="Produto ativo")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Nome do produto não pode ser vazio')
        return v.strip()
    
    @field_validator('code')
    @classmethod
    def code_strip(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v
    
    model_config = {"json_schema_extra": {
        "example": {
            "code": "PROD001",
            "name": "Notebook Dell Inspiron",
            "category": "Informática",
            "subcategoria": "Notebooks",
            "unit": "un",
            "description": "Notebook 15.6 polegadas, i5, 8GB RAM",
            "codigo_barras": "7891234567890",
            "marca": "Dell",
            "modelo": "Inspiron 15-3000",
            "peso": 2.5,
            "dimensoes": "35x25x2 cm",
            "cost_price": 2500.00,
            "sale_price": 3500.00,
            "markup": 40.00,
            "stock_qty": 10,
            "stock_min": 2,
            "estoque_maximo": 50,
            "controla_estoque": True,
            "active": True
        }
    }}


class ProductUpdate(BaseModel):
    """
    Schema para atualização parcial de produto (PATCH).
    
    Todos os campos são opcionais.
    user_id é IMUTÁVEL (isolamento protegido).
    """
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=80)
    subcategoria: Optional[str] = Field(None, max_length=80)
    unit: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None)
    
    # Identificação Estendida
    codigo_barras: Optional[str] = Field(None, max_length=50)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    
    # Características Físicas
    peso: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=3)
    dimensoes: Optional[str] = Field(None, max_length=100)
    
    # Preços
    cost_price: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2)
    sale_price: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2)
    markup: Optional[Decimal] = Field(None, ge=0, le=1000, max_digits=5, decimal_places=2)
    margem_lucro: Optional[Decimal] = Field(None, ge=-100, le=1000, max_digits=5, decimal_places=2)
    
    # Estoque
    stock_qty: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=3)
    stock_min: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=3)
    estoque_maximo: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=3)
    controla_estoque: Optional[bool] = None
    
    # Relacionamentos e Observações
    fornecedor_id: Optional[UUID] = Field(None)
    observacoes: Optional[str] = Field(None)
    
    # Status
    active: Optional[bool] = None
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('Nome do produto não pode ser vazio')
        if v:
            return v.strip()
        return v
    
    model_config = {"json_schema_extra": {
        "example": {
            "name": "Notebook Dell Inspiron (Atualizado)",
            "sale_price": 3800.00,
            "stock_qty": 15
        }
    }}


class ProductOut(BaseModel):
    """Schema de saída de produto (response)."""
    id: UUID
    user_id: UUID
    code: Optional[str]
    name: str
    category: Optional[str]
    subcategoria: Optional[str]
    unit: Optional[str]
    description: Optional[str]
    
    # Identificação Estendida
    codigo_barras: Optional[str]
    marca: Optional[str]
    modelo: Optional[str]
    
    # Características Físicas
    peso: Optional[float]
    dimensoes: Optional[str]
    
    # Preços
    cost_price: float
    sale_price: float
    markup: Optional[float]
    margem_lucro: Optional[float]
    
    # Estoque
    stock_qty: float
    stock_min: float
    estoque_maximo: Optional[float]
    controla_estoque: bool
    
    # Relacionamentos e Observações
    fornecedor_id: Optional[UUID]
    observacoes: Optional[str]
    
    # Status
    active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed Properties (do model)
    valor_estoque: Optional[float] = None
    situacao_estoque: Optional[str] = None
    margem_lucro_calculada: Optional[float] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema de resposta paginada para lista de produtos."""
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
    
    model_config = {"json_schema_extra": {
        "example": {
            "items": [],
            "total": 50,
            "page": 1,
            "page_size": 20
        }
    }}

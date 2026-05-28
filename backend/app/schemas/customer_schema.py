"""
Schemas Pydantic para Customer.
"""

from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal


class CustomerCreate(BaseModel):
    """Schema para criação de cliente."""
    person_type: Optional[Literal['PF', 'PJ']] = Field('PF', description="Tipo de pessoa: PF (Pessoa Física) ou PJ (Pessoa Jurídica)")
    name: str = Field(..., min_length=1, max_length=120, description="Nome completo (PF) ou Razão Social (PJ)")
    trade_name: Optional[str] = Field(None, max_length=120, description="Nome Fantasia (apenas PJ)")
    cpf_cnpj: Optional[str] = Field(None, min_length=11, max_length=14, description="CPF (11 dígitos) ou CNPJ (14 dígitos)")
    state_registration: Optional[str] = Field(None, max_length=20, description="Inscrição Estadual (IE)")
    email: Optional[EmailStr] = Field(None, max_length=120, description="Email")
    phone: Optional[str] = Field(None, max_length=15, description="Telefone principal (apenas dígitos)")
    phone2: Optional[str] = Field(None, max_length=15, description="Telefone alternativo (apenas dígitos)")
    cep: Optional[str] = Field(None, min_length=8, max_length=8, description="CEP (8 dígitos)")
    street: Optional[str] = Field(None, max_length=200, description="Logradouro")
    number: Optional[str] = Field(None, max_length=20, description="Número")
    address_complement: Optional[str] = Field(None, max_length=100, description="Complemento")
    neighborhood: Optional[str] = Field(None, max_length=100, description="Bairro")
    city: Optional[str] = Field(None, max_length=100, description="Cidade")
    state: Optional[str] = Field(None, min_length=2, max_length=2, description="UF (2 caracteres)")
    notes: Optional[str] = Field(None, description="Observações")
    status: Optional[Literal['active', 'inactive']] = Field('active', description="Status: active ou inactive")
    
    model_config = {"json_schema_extra": {
        "example": {
            "person_type": "PJ",
            "name": "Tech Solutions LTDA",
            "trade_name": "TechSol",
            "cpf_cnpj": "12345678000190",
            "state_registration": "123456789",
            "email": "contato@techsol.com.br",
            "phone": "11987654321",
            "phone2": "1133334444",
            "cep": "01310100",
            "street": "Avenida Paulista",
            "number": "1578",
            "address_complement": "Sala 1001",
            "neighborhood": "Bela Vista",
            "city": "São Paulo",
            "state": "SP",
            "notes": "Cliente preferencial",
            "status": "active"
        }
    }}


class CustomerUpdate(BaseModel):
    """Schema para atualização parcial (PATCH)."""
    person_type: Optional[Literal['PF', 'PJ']] = None
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    trade_name: Optional[str] = Field(None, max_length=120)
    cpf_cnpj: Optional[str] = Field(None, min_length=11, max_length=14)
    state_registration: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=15)
    phone2: Optional[str] = Field(None, max_length=15)
    cep: Optional[str] = Field(None, min_length=8, max_length=8)
    street: Optional[str] = Field(None, max_length=200)
    number: Optional[str] = Field(None, max_length=20)
    address_complement: Optional[str] = Field(None, max_length=100)
    neighborhood: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    notes: Optional[str] = None
    status: Optional[Literal['active', 'inactive']] = None


class CustomerOut(BaseModel):
    """Schema de saída de cliente (response)."""
    id: UUID
    person_type: Optional[str] = None
    name: str
    trade_name: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    state_registration: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    cep: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    address_complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

"""
Schemas Pydantic para Supplier (Fornecedor)
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


# ==================== BASE SCHEMA ====================

class SupplierBase(BaseModel):
    """Campos base compartilhados"""
    
    # Dados Principais
    nome: str = Field(..., min_length=1, max_length=150, description="Razão Social (PJ) ou Nome Completo (PF)")
    nome_fantasia: Optional[str] = Field(None, max_length=150, description="Nome Fantasia")
    tipo: str = Field(..., pattern='^(PF|PJ)$', description="PF (Pessoa Física) ou PJ (Pessoa Jurídica)")
    
    # Documentos
    cnpj_cpf: str = Field(..., max_length=20, description="CPF ou CNPJ")
    rg_ie: Optional[str] = Field(None, max_length=20, description="RG ou Inscrição Estadual")
    inscricao_estadual: Optional[str] = Field(None, max_length=20)
    inscricao_municipal: Optional[str] = Field(None, max_length=20)
    im: Optional[str] = Field(None, max_length=20, description="Inscrição Municipal (alternativo)")
    
    # Contato
    email: Optional[EmailStr] = None
    email_financeiro: Optional[EmailStr] = None
    telefone: Optional[str] = Field(None, max_length=100)
    celular: Optional[str] = Field(None, max_length=100)
    whatsapp: Optional[str] = Field(None, max_length=100)
    site: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=200)
    
    # Contato Comercial
    contato_nome: Optional[str] = Field(None, max_length=100)
    contato_cargo: Optional[str] = Field(None, max_length=100)
    contato_email: Optional[EmailStr] = None
    contato_telefone: Optional[str] = Field(None, max_length=100)
    
    # Endereço
    cep: Optional[str] = Field(None, max_length=10)
    endereco: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=2, description="UF (2 caracteres)")
    pais: Optional[str] = Field('Brasil', max_length=50)
    
    # Segmentação
    segmento: Optional[str] = Field(None, max_length=100)
    porte_empresa: Optional[str] = Field(None, max_length=20)
    origem: Optional[str] = Field(None, max_length=50)
    classificacao: Optional[str] = Field(None, max_length=50)
    categoria: Optional[str] = Field(None, max_length=50)
    categoria_fiscal: Optional[str] = Field(None, max_length=50)
    
    # Comercial
    condicoes_pagamento: Optional[str] = Field(None, max_length=100)
    prazo_entrega: Optional[str] = Field(None, max_length=50)
    forma_entrega: Optional[str] = Field(None, max_length=50)
    tempo_entrega_medio: Optional[str] = Field(None, max_length=50)
    
    # Financeiro
    limite_credito: Optional[Decimal] = Field(None, ge=0, description="Limite de crédito (>= 0)")
    prazo_pagamento_padrao: Optional[int] = Field(None, ge=0, description="Prazo em dias (>= 0)")
    desconto_padrao: Optional[Decimal] = Field(None, ge=0, le=100, description="Desconto em % (0-100)")
    
    # Datas
    data_nascimento: Optional[date] = Field(None, description="Data de nascimento (PF)")
    data_fundacao: Optional[date] = Field(None, description="Data de fundação (PJ)")
    
    # Pessoais (PF)
    genero: Optional[str] = Field(None, max_length=20)
    estado_civil: Optional[str] = Field(None, max_length=20)
    profissao: Optional[str] = Field(None, max_length=100)
    
    # Específicos
    certificacoes: Optional[str] = None
    
    # Bancário
    banco_principal: Optional[str] = Field(None, max_length=100)
    agencia: Optional[str] = Field(None, max_length=20)
    conta: Optional[str] = Field(None, max_length=30)
    pix: Optional[str] = Field(None, max_length=100, description="Chave PIX")
    
    # Gestão
    observacoes: Optional[str] = None
    observacoes_internas: Optional[str] = None
    status: Optional[str] = Field('Ativo', max_length=20)
    motivo_bloqueio: Optional[str] = Field(None, max_length=200)
    ativo: bool = Field(True, description="Soft delete")
    
    @field_validator('estado')
    @classmethod
    def validate_estado(cls, v):
        """Valida que estado seja UF válida (2 letras maiúsculas) ou vazio/None"""
        if not v or v == '':
            return None  # Aceita vazio
        if len(v) == 2:
            return v.upper()
        if len(v) > 2:
            # Se receber mais de 2, pega só os 2 primeiros e converte para maiúsculas
            return v[:2].upper()
        return v.upper()  # Se tiver 1 caractere, converte para maiúsculas
    
    @field_validator('cnpj_cpf')
    @classmethod
    def validate_documento(cls, v, info):
        """Remove formatação do documento (mantém apenas dígitos)"""
        if not v:
            raise ValueError('CNPJ/CPF é obrigatório')
        # Remove tudo que não é dígito para armazenar limpo
        doc_limpo = ''.join(filter(str.isdigit, v))
        if len(doc_limpo) < 11:
            raise ValueError('Documento deve ter pelo menos 11 dígitos (CPF) ou 14 dígitos (CNPJ)')
        return doc_limpo


# ==================== CREATE SCHEMA ====================

class SupplierCreate(SupplierBase):
    """Schema para criação de fornecedor"""
    pass


# ==================== UPDATE SCHEMA ====================

class SupplierUpdate(BaseModel):
    """
    Schema para atualização de fornecedor.
    Todos os campos são opcionais.
    """
    
    # Dados Principais
    nome: Optional[str] = Field(None, min_length=1, max_length=150)
    nome_fantasia: Optional[str] = Field(None, max_length=150)
    tipo: Optional[str] = Field(None, pattern='^(PF|PJ)$')
    
    # Documentos
    cnpj_cpf: Optional[str] = Field(None, max_length=20)
    rg_ie: Optional[str] = Field(None, max_length=20)
    inscricao_estadual: Optional[str] = Field(None, max_length=20)
    inscricao_municipal: Optional[str] = Field(None, max_length=20)
    im: Optional[str] = Field(None, max_length=20)
    
    # Contato
    email: Optional[EmailStr] = None
    email_financeiro: Optional[EmailStr] = None
    telefone: Optional[str] = Field(None, max_length=100)
    celular: Optional[str] = Field(None, max_length=100)
    whatsapp: Optional[str] = Field(None, max_length=100)
    site: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=200)
    
    # Contato Comercial
    contato_nome: Optional[str] = Field(None, max_length=100)
    contato_cargo: Optional[str] = Field(None, max_length=100)
    contato_email: Optional[EmailStr] = None
    contato_telefone: Optional[str] = Field(None, max_length=100)
    
    # Endereço
    cep: Optional[str] = Field(None, max_length=10)
    endereco: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=2)
    pais: Optional[str] = Field(None, max_length=50)
    
    # Segmentação
    segmento: Optional[str] = Field(None, max_length=100)
    porte_empresa: Optional[str] = Field(None, max_length=20)
    origem: Optional[str] = Field(None, max_length=50)
    classificacao: Optional[str] = Field(None, max_length=50)
    categoria: Optional[str] = Field(None, max_length=50)
    categoria_fiscal: Optional[str] = Field(None, max_length=50)
    
    # Comercial
    condicoes_pagamento: Optional[str] = Field(None, max_length=100)
    prazo_entrega: Optional[str] = Field(None, max_length=50)
    forma_entrega: Optional[str] = Field(None, max_length=50)
    tempo_entrega_medio: Optional[str] = Field(None, max_length=50)
    
    # Financeiro
    limite_credito: Optional[Decimal] = Field(None, ge=0)
    prazo_pagamento_padrao: Optional[int] = Field(None, ge=0)
    desconto_padrao: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Datas
    data_nascimento: Optional[date] = None
    data_fundacao: Optional[date] = None
    
    # Pessoais (PF)
    genero: Optional[str] = Field(None, max_length=20)
    estado_civil: Optional[str] = Field(None, max_length=20)
    profissao: Optional[str] = Field(None, max_length=100)
    
    # Específicos
    certificacoes: Optional[str] = None
    
    # Bancário
    banco_principal: Optional[str] = Field(None, max_length=100)
    agencia: Optional[str] = Field(None, max_length=20)
    conta: Optional[str] = Field(None, max_length=30)
    pix: Optional[str] = Field(None, max_length=100)
    
    # Gestão
    observacoes: Optional[str] = None
    observacoes_internas: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    motivo_bloqueio: Optional[str] = Field(None, max_length=200)
    ativo: Optional[bool] = None
    
    @field_validator('estado')
    @classmethod
    def validate_estado(cls, v):
        if v and len(v) == 2:
            return v.upper()
        return v
    
    @field_validator('cnpj_cpf')
    @classmethod
    def validate_documento(cls, v):
        if v:
            doc_limpo = ''.join(filter(str.isdigit, v))
            if len(doc_limpo) not in [11, 14]:
                raise ValueError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos')
            return doc_limpo
        return v


# ==================== OUTPUT SCHEMA ====================

class SupplierOut(SupplierBase):
    """
    Schema para resposta (Output).
    Inclui campos computados do modelo.
    """
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Campos computados (para facilitar no frontend)
    documento_formatado: str = Field(..., description="CPF/CNPJ formatado")
    nome_display: str = Field(..., description="Nome para exibição")
    endereco_completo: str = Field(..., description="Endereço formatado completo")
    contato_principal: str = Field(..., description="Informação do contato principal")
    is_pessoa_juridica: bool
    is_pessoa_fisica: bool
    telefone_formatado: str
    celular_formatado: str
    
    class Config:
        from_attributes = True


# ==================== LIST FILTERS ====================

class SupplierFilters(BaseModel):
    """Filtros para listagem de fornecedores"""
    search: Optional[str] = Field(None, description="Busca por nome, fantasia, documento ou email")
    tipo: Optional[str] = Field(None, pattern='^(PF|PJ)$', description="Filtrar por tipo")
    categoria: Optional[str] = Field(None, description="Filtrar por categoria")
    classificacao: Optional[str] = Field(None, description="Filtrar por classificação A/B/C/D")
    cidade: Optional[str] = Field(None, description="Filtrar por cidade")
    estado: Optional[str] = Field(None, max_length=2, description="Filtrar por UF")
    ativo: Optional[bool] = Field(True, description="Incluir inativos se False")
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

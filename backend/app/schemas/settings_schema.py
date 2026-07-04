"""
Schemas Pydantic para Settings
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class SettingsBase(BaseModel):
    """Schema base para Settings"""
    # Empresa
    company_name: Optional[str] = Field(default=None, description="Razão Social")
    trade_name: Optional[str] = Field(default=None, description="Nome Fantasia")
    cnpj: Optional[str] = Field(default=None, description="CNPJ")
    email: Optional[str] = Field(default=None, description="Email")
    phones: Optional[List[str]] = Field(default=None, description="Lista de telefones")
    
    # Endereço
    street_address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    
    # Logo
    logo_url: Optional[str] = Field(default=None, description="URL ou base64 da logo")
    
    # Dados Bancários
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    bank_agency: Optional[str] = None
    bank_account: Optional[str] = None
    pix_key: Optional[str] = None
    
    # Institucional
    mission: Optional[str] = None
    vision: Optional[str] = None
    values: Optional[List[str]] = Field(default=None, description="Valores da empresa")
    
    # Tema
    theme_primary_color: Optional[str] = None
    theme_secondary_color: Optional[str] = None
    
    # Sistema
    timezone: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    decimal_separator: Optional[str] = None
    thousand_separator: Optional[str] = None
    
    # PDF
    pdf_logo_position: Optional[str] = None
    pdf_logo_width: Optional[int] = None
    pdf_show_watermark: Optional[bool] = None
    pdf_header_text: Optional[str] = None
    pdf_footer_text: Optional[str] = None
    default_proposal_message: Optional[str] = None


class SettingsUpdate(BaseModel):
    """Schema para atualização parcial de Settings"""
    # Empresa
    company_name: Optional[str] = None
    trade_name: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    phones: Optional[List[str]] = None
    
    # Endereço
    street_address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    
    # Logo
    logo_url: Optional[str] = None
    
    # Dados Bancários
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    bank_agency: Optional[str] = None
    bank_account: Optional[str] = None
    pix_key: Optional[str] = None
    
    # Institucional
    mission: Optional[str] = None
    vision: Optional[str] = None
    values: Optional[List[str]] = None
    
    # Tema
    theme_primary_color: Optional[str] = None
    theme_secondary_color: Optional[str] = None
    
    # Sistema
    timezone: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    decimal_separator: Optional[str] = None
    thousand_separator: Optional[str] = None
    
    # PDF
    pdf_logo_position: Optional[str] = None
    pdf_logo_width: Optional[int] = None
    pdf_show_watermark: Optional[bool] = None
    pdf_header_text: Optional[str] = None
    pdf_footer_text: Optional[str] = None
    default_proposal_message: Optional[str] = None


class SettingsResponse(SettingsBase):
    """Schema para resposta de Settings"""
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    class Config:
        from_attributes = True

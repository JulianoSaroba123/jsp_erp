"""
Model Settings - Configurações do Sistema
Armazena configurações da empresa e sistema em banco de dados
"""
from sqlalchemy import Column, String, Text, TIMESTAMP, text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.types import NUMERIC

from app.database import Base


class Settings(Base):
    """
    Tabela de configurações do sistema (single-row table)
    Schema: public
    """
    __tablename__ = "settings"
    __table_args__ = (
        {'schema': 'public'},
    )

    # ID fixo (sempre UUID específico para garantir single row)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("'00000000-0000-0000-0000-000000000001'::uuid"),
        comment="ID fixo para garantir registro único"
    )
    
    # ==================== DADOS DA EMPRESA ====================
    company_name = Column(String(255), nullable=True, comment="Razão Social")
    trade_name = Column(String(255), nullable=True, comment="Nome Fantasia")
    cnpj = Column(String(18), nullable=True, comment="CNPJ formatado")
    email = Column(String(255), nullable=True, comment="Email principal")
    phones = Column(ARRAY(Text), nullable=True, comment="Lista de telefones")
    
    # Endereço
    street_address = Column(String(255), nullable=True, comment="Endereço completo")
    neighborhood = Column(String(100), nullable=True, comment="Bairro")
    city = Column(String(100), nullable=True, comment="Cidade")
    state = Column(String(2), nullable=True, comment="Estado (UF)")
    postal_code = Column(String(9), nullable=True, comment="CEP")
    country = Column(String(100), nullable=True, comment="País")
    latitude = Column(NUMERIC(10, 8), nullable=True, comment="Latitude")
    longitude = Column(NUMERIC(11, 8), nullable=True, comment="Longitude")
    
    # Logo
    logo_url = Column(Text, nullable=True, comment="URL ou base64 da logo")
    
    # Dados Bancários
    bank_name = Column(String(100), nullable=True, comment="Nome do banco")
    bank_code = Column(String(10), nullable=True, comment="Código do banco")
    bank_agency = Column(String(20), nullable=True, comment="Agência")
    bank_account = Column(String(30), nullable=True, comment="Conta")
    pix_key = Column(String(255), nullable=True, comment="Chave PIX")
    
    # Institucional
    mission = Column(Text, nullable=True, comment="Missão da empresa")
    vision = Column(Text, nullable=True, comment="Visão da empresa")
    values = Column(ARRAY(Text), nullable=True, comment="Valores (array)")
    
    # ==================== CONFIGURAÇÕES DO TEMA ====================
    theme_primary_color = Column(String(7), nullable=True, comment="Cor primária do tema")
    theme_secondary_color = Column(String(7), nullable=True, comment="Cor secundária do tema")
    
    # ==================== CONFIGURAÇÕES DO SISTEMA ====================
    timezone = Column(String(50), nullable=True, comment="Timezone")
    language = Column(String(5), nullable=True, comment="Idioma")
    currency = Column(String(3), nullable=True, comment="Moeda")
    date_format = Column(String(20), nullable=True, comment="Formato de data")
    decimal_separator = Column(String(1), nullable=True, comment="Separador decimal")
    thousand_separator = Column(String(1), nullable=True, comment="Separador de milhar")
    
    # PDF
    pdf_logo_position = Column(String(20), nullable=True, comment="Posição do logo no PDF")
    pdf_logo_width = Column(Integer, nullable=True, comment="Largura do logo no PDF")
    pdf_show_watermark = Column(Boolean, nullable=True, comment="Mostrar marca d'água")
    pdf_header_text = Column(Text, nullable=True, comment="Texto no cabeçalho do PDF")
    pdf_footer_text = Column(Text, nullable=True, comment="Texto no rodapé do PDF")
    default_proposal_message = Column(Text, nullable=True, comment="Mensagem padrão de proposta")
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("now()"), onupdate=text("now()"), nullable=True)

    def __repr__(self):
        return f"<Settings(company_name='{self.company_name}')>"

"""
Model SQLAlchemy para tabela core.customers
"""
from sqlalchemy import Column, String, Text, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Customer(Base):
    """
    Tabela de clientes.
    Schema: core
    """
    __tablename__ = "customers"
    __table_args__ = {"schema": "core"}

    # Colunas
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    # Tipo de pessoa (PF ou PJ)
    person_type = Column(String(2), nullable=True, default='PF')  # 'PF' ou 'PJ'
    
    # Dados básicos
    name = Column(String(120), nullable=False, index=True)  # Nome completo (PF) ou Razão Social (PJ)
    trade_name = Column(String(120), nullable=True)  # Nome Fantasia (apenas PJ)
    cpf_cnpj = Column(String(14), nullable=True, index=True)  # Apenas dígitos
    state_registration = Column(String(20), nullable=True)  # Inscrição Estadual (IE)
    
    # Contato
    email = Column(String(120), nullable=True)
    phone = Column(String(15), nullable=True)  # Telefone principal
    phone2 = Column(String(15), nullable=True)  # Telefone alternativo
    
    # Endereço
    cep = Column(String(8), nullable=True)  # Apenas dígitos
    street = Column(String(200), nullable=True)
    number = Column(String(20), nullable=True)
    address_complement = Column(String(100), nullable=True)  # Complemento
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)  # UF
    
    # Informações adicionais
    notes = Column(Text, nullable=True)  # Observações
    status = Column(String(10), nullable=False, default='active')  # 'active' ou 'inactive'
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    
    # Soft Delete
    deleted_at = Column(TIMESTAMP, nullable=True, index=True)

    def __repr__(self):
        return f"<Customer(id={self.id}, name={self.name})>"

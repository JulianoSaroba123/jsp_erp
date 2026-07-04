"""
Modelo Supplier (Fornecedor)
Suporta Pessoa Física (PF) e Pessoa Jurídica (PJ)
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, Date, ForeignKey, Numeric, CheckConstraint, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Supplier(Base):
    """
    Modelo de Fornecedor com ~52 campos.
    Suporta PF (Pessoa Física) e PJ (Pessoa Jurídica) com campos específicos.
    """
    
    __tablename__ = "suppliers"
    __table_args__ = (
        CheckConstraint("tipo IN ('PF', 'PJ')", name='ck_suppliers_tipo'),
        CheckConstraint('limite_credito >= 0', name='ck_suppliers_limite_credito'),
        CheckConstraint('desconto_padrao >= 0 AND desconto_padrao <= 100', name='ck_suppliers_desconto_padrao'),
        CheckConstraint('prazo_pagamento_padrao >= 0', name='ck_suppliers_prazo_pagamento'),
        CheckConstraint("estado IS NULL OR LENGTH(estado) = 2", name='ck_suppliers_estado_length'),
        {'schema': 'core'}
    )
    
    # === Identificação ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False)
    
    # === Dados Principais ===
    nome = Column(String(150), nullable=False, comment='Razão Social (PJ) ou Nome Completo (PF)')
    nome_fantasia = Column(String(150), nullable=True, comment='Nome Fantasia da empresa')
    tipo = Column(String(2), nullable=False, comment='PF (Pessoa Física) ou PJ (Pessoa Jurídica)')
    
    # === Documentos ===
    cnpj_cpf = Column(String(20), nullable=False, comment='CPF (11 dígitos) ou CNPJ (14 dígitos)')
    rg_ie = Column(String(20), nullable=True, comment='RG (PF) ou Inscrição Estadual (PJ)')
    inscricao_estadual = Column(String(20), nullable=True, comment='Inscrição Estadual (PJ)')
    inscricao_municipal = Column(String(20), nullable=True, comment='Inscrição Municipal (PJ)')
    im = Column(String(20), nullable=True, comment='Inscrição Municipal (alternativo)')
    
    # === Contato ===
    email = Column(String(150), nullable=True, comment='Email principal')
    email_financeiro = Column(String(150), nullable=True, comment='Email do setor financeiro')
    telefone = Column(String(20), nullable=True, comment='Telefone fixo')
    celular = Column(String(20), nullable=True, comment='Celular')
    whatsapp = Column(String(20), nullable=True, comment='WhatsApp')
    site = Column(String(200), nullable=True, comment='Website (alternativo)')
    website = Column(String(200), nullable=True, comment='Website principal')
    
    # === Contato Comercial ===
    contato_nome = Column(String(100), nullable=True, comment='Nome do contato responsável')
    contato_cargo = Column(String(100), nullable=True, comment='Cargo do contato')
    contato_email = Column(String(150), nullable=True, comment='Email do contato')
    contato_telefone = Column(String(20), nullable=True, comment='Telefone do contato')
    
    # === Endereço ===
    cep = Column(String(10), nullable=True, comment='CEP (8 dígitos)')
    endereco = Column(String(200), nullable=True, comment='Logradouro')
    numero = Column(String(20), nullable=True, comment='Número do imóvel')
    complemento = Column(String(100), nullable=True, comment='Complemento')
    bairro = Column(String(100), nullable=True, comment='Bairro')
    cidade = Column(String(100), nullable=True, comment='Cidade')
    estado = Column(String(2), nullable=True, comment='UF (sigla)')
    pais = Column(String(50), nullable=True, default='Brasil', comment='País')
    
    # === Segmentação ===
    segmento = Column(String(100), nullable=True, comment='Segmento de atuação')
    porte_empresa = Column(String(20), nullable=True, comment='MEI, Micro, Pequena, Média, Grande')
    origem = Column(String(50), nullable=True, comment='Como nos conheceu')
    classificacao = Column(String(50), nullable=True, comment='Classe A/B/C/D')
    categoria = Column(String(50), nullable=True, comment='Categoria comercial')
    categoria_fiscal = Column(String(50), nullable=True, comment='Categoria fiscal')
    
    # === Comercial ===
    condicoes_pagamento = Column(String(100), nullable=True, comment='Ex: 30/60 dias')
    prazo_entrega = Column(String(50), nullable=True, comment='Ex: 5-10 dias úteis')
    forma_entrega = Column(String(50), nullable=True, comment='Ex: FOB, CIF')
    tempo_entrega_medio = Column(String(50), nullable=True, comment='Tempo médio')
    
    # === Financeiro ===
    limite_credito = Column(Numeric(15, 2), nullable=True, comment='Limite de crédito aprovado')
    prazo_pagamento_padrao = Column(Integer, nullable=True, comment='Prazo padrão em dias')
    desconto_padrao = Column(Numeric(5, 2), nullable=True, comment='Desconto padrão em %')
    
    # === Datas ===
    data_nascimento = Column(Date, nullable=True, comment='Data de nascimento (PF)')
    data_fundacao = Column(Date, nullable=True, comment='Data de fundação (PJ)')
    
    # === Pessoais (PF) ===
    genero = Column(String(20), nullable=True, comment='Masculino, Feminino, Outros')
    estado_civil = Column(String(20), nullable=True, comment='Solteiro, Casado, etc')
    profissao = Column(String(100), nullable=True, comment='Profissão (PF)')
    
    # === Específicos ===
    certificacoes = Column(Text, nullable=True, comment='Certificações')
    
    # === Bancário ===
    banco_principal = Column(String(100), nullable=True, comment='Nome do banco')
    agencia = Column(String(20), nullable=True, comment='Agência')
    conta = Column(String(30), nullable=True, comment='Conta')
    pix = Column(String(100), nullable=True, comment='Chave PIX')
    
    # === Gestão ===
    observacoes = Column(Text, nullable=True, comment='Observações gerais')
    observacoes_internas = Column(Text, nullable=True, comment='Observações internas')
    status = Column(String(20), nullable=True, default='Ativo', comment='Ativo, Inativo, Bloqueado')
    motivo_bloqueio = Column(String(200), nullable=True, comment='Motivo do bloqueio')
    ativo = Column(Boolean, nullable=False, default=True, comment='Soft delete')
    
    # === Timestamps ===
    created_at = Column(TIMESTAMP, server_default=text("now()"), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("now()"), onupdate=text("now()"), nullable=False)
    
    # === Relacionamentos ===
    # user = relationship("User", back_populates="suppliers")  # Se necessário
    
    # ==================== COMPUTED PROPERTIES ====================
    
    @property
    def documento_formatado(self) -> str:
        """
        Formata CPF/CNPJ:
        - CPF: 000.000.000-00 (11 dígitos)
        - CNPJ: 00.000.000/0000-00 (14 dígitos)
        """
        if not self.cnpj_cpf:
            return ''
        
        # Remove tudo que não é dígito
        doc = ''.join(filter(str.isdigit, self.cnpj_cpf))
        
        if len(doc) == 11:  # CPF
            return f'{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}'
        elif len(doc) == 14:  # CNPJ
            return f'{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}'
        else:
            return self.cnpj_cpf  # Retorna original se formato inválido
    
    @property
    def nome_display(self) -> str:
        """
        Nome para exibição:
        - PJ: "Fantasia (Razão Social)" ou só "Razão Social"
        - PF: "Nome Completo"
        """
        if self.tipo == 'PJ' and self.nome_fantasia:
            return f"{self.nome_fantasia} ({self.nome})"
        return self.nome
    
    @property
    def endereco_completo(self) -> str:
        """
        Endereço formatado completo:
        "Rua ABC, 123 - Apt 45 - Bairro - Cidade/UF - CEP 12345-678"
        """
        partes = []
        
        if self.endereco:
            endereco_base = self.endereco
            if self.numero:
                endereco_base += f', {self.numero}'
            if self.complemento:
                endereco_base += f' - {self.complemento}'
            partes.append(endereco_base)
        
        if self.bairro:
            partes.append(self.bairro)
        
        if self.cidade or self.estado:
            cidade_estado = self.cidade or ''
            if self.estado:
                cidade_estado += f'/{self.estado}' if cidade_estado else self.estado
            partes.append(cidade_estado)
        
        if self.cep:
            cep_formatado = self.cep
            if len(self.cep.replace('-', '').replace('.', '')) == 8:
                cep_limpo = ''.join(filter(str.isdigit, self.cep))
                cep_formatado = f'{cep_limpo[:5]}-{cep_limpo[5:]}'
            partes.append(f'CEP {cep_formatado}')
        
        return ' - '.join(partes) if partes else ''
    
    @property
    def contato_principal(self) -> str:
        """
        Informação do contato principal:
        "João Silva (Gerente Comercial)"
        """
        if self.contato_nome:
            if self.contato_cargo:
                return f"{self.contato_nome} ({self.contato_cargo})"
            return self.contato_nome
        return ''
    
    @property
    def is_pessoa_juridica(self) -> bool:
        """Verifica se é Pessoa Jurídica"""
        return self.tipo == 'PJ'
    
    @property
    def is_pessoa_fisica(self) -> bool:
        """Verifica se é Pessoa Física"""
        return self.tipo == 'PF'
    
    @property
    def telefone_formatado(self) -> str:
        """Formata telefone: (11) 1234-5678 ou (11) 99999-9999"""
        if not self.telefone:
            return ''
        
        digitos = ''.join(filter(str.isdigit, self.telefone))
        
        if len(digitos) == 10:
            return f'({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}'
        elif len(digitos) == 11:
            return f'({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}'
        else:
            return self.telefone
    
    @property
    def celular_formatado(self) -> str:
        """Formata celular: (11) 99999-9999"""
        if not self.celular:
            return ''
        
        digitos = ''.join(filter(str.isdigit, self.celular))
        
        if len(digitos) == 11:
            return f'({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}'
        else:
            return self.celular
    
    # ==================== MÉTODOS ====================
    
    def validar_documento(self) -> tuple[bool, str]:
        """
        Valida CPF ou CNPJ (validação básica de formato)
        Retorna: (bool, mensagem)
        """
        if not self.cnpj_cpf:
            return False, "Documento é obrigatório"
        
        doc = ''.join(filter(str.isdigit, self.cnpj_cpf))
        
        if self.tipo == 'PF':
            if len(doc) != 11:
                return False, "CPF deve ter 11 dígitos"
            # Aqui poderia adicionar validação de dígitos verificadores
            return True, "CPF válido"
        
        elif self.tipo == 'PJ':
            if len(doc) != 14:
                return False, "CNPJ deve ter 14 dígitos"
            # Aqui poderia adicionar validação de dígitos verificadores
            return True, "CNPJ válido"
        
        return False, "Tipo de pessoa inválido"
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, nome='{self.nome}', tipo='{self.tipo}')>"

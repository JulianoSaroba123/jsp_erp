"""create suppliers table

Revision ID: 010_create_suppliers
Revises: 009_extend_products
Create Date: 2026-03-05 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision = '010_create_suppliers'
down_revision = '009_extend_products'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Cria tabela core.suppliers com ~50 campos para gerenciamento completo de fornecedores.
    Suporta Pessoa Física (PF) e Pessoa Jurídica (PJ) com campos específicos.
    """
    
    op.create_table(
        'suppliers',
        
        # === Identificação ===
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False),
        
        # === Dados Principais ===
        sa.Column('nome', sa.String(150), nullable=False, comment='Razão Social (PJ) ou Nome Completo (PF)'),
        sa.Column('nome_fantasia', sa.String(150), nullable=True, comment='Nome Fantasia da empresa'),
        sa.Column('tipo', sa.String(2), nullable=False, comment='PF (Pessoa Física) ou PJ (Pessoa Jurídica)'),
        
        # === Documentos ===
        sa.Column('cnpj_cpf', sa.String(20), nullable=False, unique=True, comment='CPF (11 dígitos) ou CNPJ (14 dígitos)'),
        sa.Column('rg_ie', sa.String(20), nullable=True, comment='RG (PF) ou Inscrição Estadual (PJ)'),
        sa.Column('inscricao_estadual', sa.String(20), nullable=True, comment='Inscrição Estadual (PJ)'),
        sa.Column('inscricao_municipal', sa.String(20), nullable=True, comment='Inscrição Municipal (PJ)'),
        sa.Column('im', sa.String(20), nullable=True, comment='Inscrição Municipal (alternativo)'),
        
        # === Contato ===
        sa.Column('email', sa.String(150), nullable=True, comment='Email principal'),
        sa.Column('email_financeiro', sa.String(150), nullable=True, comment='Email do setor financeiro'),
        sa.Column('telefone', sa.String(20), nullable=True, comment='Telefone fixo'),
        sa.Column('celular', sa.String(20), nullable=True, comment='Celular'),
        sa.Column('whatsapp', sa.String(20), nullable=True, comment='WhatsApp'),
        sa.Column('site', sa.String(200), nullable=True, comment='Website (alternativo)'),
        sa.Column('website', sa.String(200), nullable=True, comment='Website principal'),
        
        # === Contato Comercial (Pessoa Responsável) ===
        sa.Column('contato_nome', sa.String(100), nullable=True, comment='Nome do contato responsável'),
        sa.Column('contato_cargo', sa.String(100), nullable=True, comment='Cargo do contato'),
        sa.Column('contato_email', sa.String(150), nullable=True, comment='Email do contato'),
        sa.Column('contato_telefone', sa.String(20), nullable=True, comment='Telefone do contato'),
        
        # === Endereço Completo ===
        sa.Column('cep', sa.String(10), nullable=True, comment='CEP (8 dígitos)'),
        sa.Column('endereco', sa.String(200), nullable=True, comment='Logradouro (Rua, Avenida, etc)'),
        sa.Column('numero', sa.String(20), nullable=True, comment='Número do imóvel'),
        sa.Column('complemento', sa.String(100), nullable=True, comment='Complemento (Apt, Sala, etc)'),
        sa.Column('bairro', sa.String(100), nullable=True, comment='Bairro'),
        sa.Column('cidade', sa.String(100), nullable=True, comment='Cidade'),
        sa.Column('estado', sa.String(2), nullable=True, comment='UF (sigla do estado)'),
        sa.Column('pais', sa.String(50), nullable=True, default='Brasil', comment='País'),
        
        # === Segmentação e Classificação ===
        sa.Column('segmento', sa.String(100), nullable=True, comment='Segmento de atuação (ex: Tecnologia, Comércio)'),
        sa.Column('porte_empresa', sa.String(20), nullable=True, comment='MEI, Micro, Pequena, Média, Grande'),
        sa.Column('origem', sa.String(50), nullable=True, comment='Como nos conheceu (Indicação, Google, etc)'),
        sa.Column('classificacao', sa.String(50), nullable=True, comment='Classe A/B/C/D - Premium/Bom/Regular/Atenção'),
        sa.Column('categoria', sa.String(50), nullable=True, comment='Categoria comercial (Equipamentos, Serviços, etc)'),
        sa.Column('categoria_fiscal', sa.String(50), nullable=True, comment='Categoria fiscal'),
        
        # === Informações Comerciais ===
        sa.Column('condicoes_pagamento', sa.String(100), nullable=True, comment='Ex: 30/60 dias, À vista'),
        sa.Column('prazo_entrega', sa.String(50), nullable=True, comment='Ex: 5-10 dias úteis'),
        sa.Column('forma_entrega', sa.String(50), nullable=True, comment='Ex: FOB, CIF, Transportadora'),
        sa.Column('tempo_entrega_medio', sa.String(50), nullable=True, comment='Tempo médio de entrega'),
        
        # === Financeiro ===
        sa.Column('limite_credito', sa.Numeric(15, 2), nullable=True, comment='Limite de crédito aprovado'),
        sa.Column('prazo_pagamento_padrao', sa.Integer, nullable=True, comment='Prazo padrão em dias'),
        sa.Column('desconto_padrao', sa.Numeric(5, 2), nullable=True, comment='Desconto padrão em %'),
        
        # === Datas ===
        sa.Column('data_nascimento', sa.Date, nullable=True, comment='Data de nascimento (PF)'),
        sa.Column('data_fundacao', sa.Date, nullable=True, comment='Data de fundação (PJ)'),
        
        # === Campos Pessoais (PF) ===
        sa.Column('genero', sa.String(20), nullable=True, comment='Masculino, Feminino, Outros'),
        sa.Column('estado_civil', sa.String(20), nullable=True, comment='Solteiro, Casado, Divorciado, Viúvo'),
        sa.Column('profissao', sa.String(100), nullable=True, comment='Profissão (PF)'),
        
        # === Específicos ===
        sa.Column('certificacoes', sa.Text, nullable=True, comment='Certificações da empresa'),
        
        # === Dados Bancários ===
        sa.Column('banco_principal', sa.String(100), nullable=True, comment='Nome do banco principal'),
        sa.Column('agencia', sa.String(20), nullable=True, comment='Agência bancária'),
        sa.Column('conta', sa.String(30), nullable=True, comment='Conta bancária'),
        sa.Column('pix', sa.String(100), nullable=True, comment='Chave PIX (CPF/CNPJ/Email/Telefone/Aleatória)'),
        
        # === Observações e Gestão ===
        sa.Column('observacoes', sa.Text, nullable=True, comment='Observações gerais (visível)'),
        sa.Column('observacoes_internas', sa.Text, nullable=True, comment='Observações internas (não visível ao fornecedor)'),
        sa.Column('status', sa.String(20), nullable=True, default='Ativo', comment='Ativo, Inativo, Bloqueado'),
        sa.Column('motivo_bloqueio', sa.String(200), nullable=True, comment='Motivo do bloqueio (se aplicável)'),
        sa.Column('ativo', sa.Boolean, nullable=False, default=True, comment='Soft delete'),
        
        # === Auditoria ===
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        schema='core'
    )
    
    # === Índices para Performance ===
    # Índice único composto para garantir documento único por usuário
    op.create_index(
        'ix_suppliers_user_documento',
        'suppliers',
        ['user_id', 'cnpj_cpf'],
        unique=True,
        schema='core'
    )
    
    # Índice para busca por nome/fantasia (case-insensitive com ILIKE)
    op.create_index(
        'ix_suppliers_nome',
        'suppliers',
        ['nome'],
        schema='core'
    )
    
    op.create_index(
        'ix_suppliers_nome_fantasia',
        'suppliers',
        ['nome_fantasia'],
        schema='core'
    )
    
    # Índice para filtro por tipo (PF/PJ)
    op.create_index(
        'ix_suppliers_tipo',
        'suppliers',
        ['tipo'],
        schema='core'
    )
    
    # Índice para filtro por categoria
    op.create_index(
        'ix_suppliers_categoria',
        'suppliers',
        ['categoria'],
        schema='core'
    )
    
    # Índice para filtro por classificação (A/B/C/D)
    op.create_index(
        'ix_suppliers_classificacao',
        'suppliers',
        ['classificacao'],
        schema='core'
    )
    
    # Índice para busca por email
    op.create_index(
        'ix_suppliers_email',
        'suppliers',
        ['email'],
        schema='core'
    )
    
    # Índice para soft delete (ativo)
    op.create_index(
        'ix_suppliers_ativo',
        'suppliers',
        ['ativo'],
        schema='core'
    )
    
    # Índice composto para listagem eficiente (user + ativo)
    op.create_index(
        'ix_suppliers_user_ativo',
        'suppliers',
        ['user_id', 'ativo'],
        schema='core'
    )
    
    # Índice para busca por cidade/estado
    op.create_index(
        'ix_suppliers_cidade_estado',
        'suppliers',
        ['cidade', 'estado'],
        schema='core'
    )
    
    # === Constraints ===
    # Tipo deve ser PF ou PJ
    op.create_check_constraint(
        'ck_suppliers_tipo',
        'suppliers',
        "tipo IN ('PF', 'PJ')",
        schema='core'
    )
    
    # Limite de crédito não pode ser negativo
    op.create_check_constraint(
        'ck_suppliers_limite_credito',
        'suppliers',
        'limite_credito >= 0',
        schema='core'
    )
    
    # Desconto padrão entre 0 e 100%
    op.create_check_constraint(
        'ck_suppliers_desconto_padrao',
        'suppliers',
        'desconto_padrao >= 0 AND desconto_padrao <= 100',
        schema='core'
    )
    
    # Prazo de pagamento padrão não pode ser negativo
    op.create_check_constraint(
        'ck_suppliers_prazo_pagamento',
        'suppliers',
        'prazo_pagamento_padrao >= 0',
        schema='core'
    )
    
    # Estado deve ter exatamente 2 caracteres (UF)
    op.create_check_constraint(
        'ck_suppliers_estado_length',
        'suppliers',
        "estado IS NULL OR LENGTH(estado) = 2",
        schema='core'
    )


def downgrade() -> None:
    """Remove tabela suppliers e todos os índices/constraints"""
    op.drop_table('suppliers', schema='core')

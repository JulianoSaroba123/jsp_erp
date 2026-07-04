"""Aplicar migration 010 - Create suppliers table"""
from sqlalchemy import text
from app.security.deps import get_db

# SQL da migration 010 (apenas CREATE TABLE e índices)
sql_create_table = """
CREATE TABLE core.suppliers (
    -- Identificação
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    
    -- Dados Principais
    nome VARCHAR(150) NOT NULL,
    nome_fantasia VARCHAR(150),
    tipo VARCHAR(2) NOT NULL CHECK (tipo IN ('PF', 'PJ')),
    
    -- Documentos
    cnpj_cpf VARCHAR(20) NOT NULL,
    rg_ie VARCHAR(20),
    inscricao_estadual VARCHAR(20),
    inscricao_municipal VARCHAR(20),
    im VARCHAR(20),
    
    -- Contato
    email VARCHAR(150),
    email_financeiro VARCHAR(150),
    telefone VARCHAR(20),
    celular VARCHAR(20),
    whatsapp VARCHAR(20),
    site VARCHAR(200),
    website VARCHAR(200),
    
    -- Contato Comercial
    contato_nome VARCHAR(100),
    contato_cargo VARCHAR(100),
    contato_email VARCHAR(150),
    contato_telefone VARCHAR(20),
    
    -- Endereço
    cep VARCHAR(10),
    endereco VARCHAR(200),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2) CHECK (estado IS NULL OR LENGTH(estado) = 2),
    pais VARCHAR(50) DEFAULT 'Brasil',
    
    -- Segmentação
    segmento VARCHAR(100),
    porte_empresa VARCHAR(20),
    origem VARCHAR(50),
    classificacao VARCHAR(50),
    categoria VARCHAR(50),
    categoria_fiscal VARCHAR(50),
    
    -- Comercial
    condicoes_pagamento VARCHAR(100),
    prazo_entrega VARCHAR(50),
    forma_entrega VARCHAR(50),
    tempo_entrega_medio VARCHAR(50),
    
    -- Financeiro
    limite_credito NUMERIC(15,2) CHECK (limite_credito >= 0),
    prazo_pagamento_padrao INTEGER CHECK (prazo_pagamento_padrao >= 0),
    desconto_padrao NUMERIC(5,2) CHECK (desconto_padrao >= 0 AND desconto_padrao <= 100),
    
    -- Datas
    data_nascimento DATE,
    data_fundacao DATE,
    
    -- Pessoais PF
    genero VARCHAR(20),
    estado_civil VARCHAR(20),
    profissao VARCHAR(100),
    
    -- Específicos
    certificacoes TEXT,
    
    -- Bancário
    banco_principal VARCHAR(100),
    agencia VARCHAR(20),
    conta VARCHAR(30),
    pix VARCHAR(100),
    
    -- Gestão
    observacoes TEXT,
    observacoes_internas TEXT,
    status VARCHAR(20) DEFAULT 'Ativo',
    motivo_bloqueio VARCHAR(200),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Auditoria
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

# Índices
indices = [
    "CREATE UNIQUE INDEX ix_suppliers_user_documento ON core.suppliers (user_id, cnpj_cpf);",
    "CREATE INDEX ix_suppliers_nome ON core.suppliers (nome);",
    "CREATE INDEX ix_suppliers_nome_fantasia ON core.suppliers (nome_fantasia);",
    "CREATE INDEX ix_suppliers_tipo ON core.suppliers (tipo);",
    "CREATE INDEX ix_suppliers_categoria ON core.suppliers (categoria);",
    "CREATE INDEX ix_suppliers_classificacao ON core.suppliers (classificacao);",
    "CREATE INDEX ix_suppliers_email ON core.suppliers (email);",
    "CREATE INDEX ix_suppliers_ativo ON core.suppliers (ativo);",
    "CREATE INDEX ix_suppliers_user_ativo ON core.suppliers (user_id, ativo);",
    "CREATE INDEX ix_suppliers_cidade_estado ON core.suppliers (cidade, estado);"
]

# Atualizar versão do alembic
sql_update_version = """
UPDATE core.alembic_version SET version_num = '010_create_suppliers';
"""

db = next(get_db())

try:
    print('🚀 Criando tabela suppliers...')
    db.execute(text(sql_create_table))
    print('✅ Tabela criada!')
    
    print('📊 Criando índices...')
    for idx_sql in indices:
        db.execute(text(idx_sql))
    print(f'✅ {len(indices)} índices criados!')
    
    print('🔄 Atualizando versão do Alembic...')
    db.execute(text(sql_update_version))
    print('✅ Versão atualizada para 010_create_suppliers!')
    
    db.commit()
    print('='*50)
    print('✅ Migration 010 aplicada com sucesso!')
    print('='*50)
    
except Exception as e:
    db.rollback()
    print(f'❌ Erro: {e}')
finally:
    db.close()

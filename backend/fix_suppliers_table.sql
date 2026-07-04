-- Script para recriar tabela suppliers com estrutura completa (52 campos)
-- Baseado em backend/app/models/supplier.py e migration 010

CREATE TABLE core.suppliers (
    -- === Identificação ===
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    
    -- === Dados Principais ===
    nome VARCHAR(150) NOT NULL, -- Razão Social (PJ) ou Nome Completo (PF)
    nome_fantasia VARCHAR(150), -- Nome Fantasia
    tipo VARCHAR(2) NOT NULL CHECK (tipo IN ('PF', 'PJ')),
    
    -- === Documentos ===
    cnpj_cpf VARCHAR(20) NOT NULL UNIQUE,
    rg_ie VARCHAR(20),
    inscricao_estadual VARCHAR(20),
    inscricao_municipal VARCHAR(20),
    im VARCHAR(20),
    
    -- === Contato ===
    email VARCHAR(150),
    email_financeiro VARCHAR(150),
    telefone VARCHAR(20),
    celular VARCHAR(20),
    whatsapp VARCHAR(20),
    site VARCHAR(200),
    website VARCHAR(200),
    
    -- === Contato Comercial ===
    contato_nome VARCHAR(100),
    contato_cargo VARCHAR(100),
    contato_email VARCHAR(150),
    contato_telefone VARCHAR(20),
    
    -- === Endereço ===
    cep VARCHAR(10),
    endereco VARCHAR(200),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2) CHECK (estado IS NULL OR LENGTH(estado) = 2),
    pais VARCHAR(50) DEFAULT 'Brasil',
    
    -- === Segmentação ===
    segmento VARCHAR(100),
    porte_empresa VARCHAR(20),
    origem VARCHAR(50),
    classificacao VARCHAR(50),
    categoria VARCHAR(50),
    categoria_fiscal VARCHAR(50),
    
    -- === Comercial ===
    condicoes_pagamento VARCHAR(100),
    prazo_entrega VARCHAR(50),
    forma_entrega VARCHAR(50),
    tempo_entrega_medio VARCHAR(50),
    
    -- === Financeiro ===
    limite_credito NUMERIC(15,2) CHECK (limite_credito IS NULL OR limite_credito >= 0),
    prazo_pagamento_padrao INTEGER CHECK (prazo_pagamento_padrao IS NULL OR prazo_pagamento_padrao >= 0),
    desconto_padrao NUMERIC(5,2) CHECK (desconto_padrao IS NULL OR (desconto_padrao >= 0 AND desconto_padrao <= 100)),
    
    -- === Datas ===
    data_nascimento DATE,
    data_fundacao DATE,
    
    -- === Pessoais (PF) ===
    genero VARCHAR(20),
    estado_civil VARCHAR(20),
    profissao VARCHAR(100),
    
    -- === Específicos ===
    certificacoes TEXT,
    
    -- === Dados Bancários ===
    banco_principal VARCHAR(100),
    agencia VARCHAR(20),
    conta VARCHAR(30),
    pix VARCHAR(100),
    
    -- === Observações ===
    observacoes TEXT,
    observacoes_internas TEXT,
    
    -- === Status ===
    status VARCHAR(20) DEFAULT 'ativo',
    motivo_bloqueio TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    
    -- === Auditoria ===
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    deleted_by UUID
);

-- Índices
CREATE INDEX idx_suppliers_user_id ON core.suppliers(user_id);
CREATE INDEX idx_suppliers_cnpj_cpf ON core.suppliers(cnpj_cpf);
CREATE INDEX idx_suppliers_tipo ON core.suppliers(tipo);
CREATE INDEX idx_suppliers_ativo ON core.suppliers(ativo);
CREATE INDEX idx_suppliers_deleted_at ON core.suppliers(deleted_at);

-- Restaurar FK em financial_entries
ALTER TABLE core.financial_entries 
ADD CONSTRAINT fk_financial_entries_supplier 
FOREIGN KEY (supplier_id) REFERENCES core.suppliers(id) ON DELETE SET NULL;

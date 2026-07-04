-- Script para criar tabela core.settings manualmente
-- Execute este script se a migration não criar a tabela

CREATE TABLE IF NOT EXISTS core.settings (
    id UUID PRIMARY KEY DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    
    -- Empresa
    company_name VARCHAR(200) NOT NULL DEFAULT '',
    trade_name VARCHAR(200),
    cnpj VARCHAR(18),
    email VARCHAR(150),
    phone VARCHAR(20),
    phone_2 VARCHAR(20),
    website VARCHAR(200),
    
    -- Endereço
    cep VARCHAR(10),
    street VARCHAR(200),
    number VARCHAR(20),
    neighborhood VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(2),
    
    -- Logo
    logo_url TEXT,
    
    -- Bancário
    bank_name VARCHAR(100),
    bank_agency VARCHAR(20),
    bank_account VARCHAR(30),
    pix_key VARCHAR(100),
    
    -- Institucional
    mission TEXT,
    vision TEXT,
    values TEXT,
    
    -- Sistema
    theme VARCHAR(10) NOT NULL DEFAULT 'light',
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Sao_Paulo',
    currency VARCHAR(3) NOT NULL DEFAULT 'BRL',
    
    -- PDF
    pdf_header_text TEXT,
    pdf_footer_text TEXT,
    default_proposal_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Popular com dados do .env (se não existir):
INSERT INTO core.settings (id, company_name, cnpj, city, state)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'JSP Automação Industrial & Solar',
    '41.280.764/0001-65',
    'Tietê',
    'SP'
)
ON CONFLICT (id) DO NOTHING;

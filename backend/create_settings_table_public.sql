-- Script para criar tabela public.settings
-- Schema correto: public (não core)

CREATE TABLE IF NOT EXISTS public.settings (
    id UUID PRIMARY KEY DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    
    -- Empresa
    company_name VARCHAR(255),
    trade_name VARCHAR(255),
    cnpj VARCHAR(18),
    email VARCHAR(255),
    phones TEXT[],
    
    -- Endereço
    street_address VARCHAR(255),
    neighborhood VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(2),
    postal_code VARCHAR(9),
    country VARCHAR(100),
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    
    -- Logo
    logo_url TEXT,
    
    -- Bancário
    bank_name VARCHAR(100),
    bank_code VARCHAR(10),
    bank_agency VARCHAR(20),
    bank_account VARCHAR(30),
    pix_key VARCHAR(255),
    
    -- Institucional
    mission TEXT,
    vision TEXT,
    values TEXT[],
    
    -- Tema
    theme_primary_color VARCHAR(7),
    theme_secondary_color VARCHAR(7),
    
    -- Sistema
    timezone VARCHAR(50),
    language VARCHAR(5),
    currency VARCHAR(3),
    date_format VARCHAR(20),
    decimal_separator VARCHAR(1),
    thousand_separator VARCHAR(1),
    
    -- PDF
    pdf_logo_position VARCHAR(20),
    pdf_logo_width INTEGER,
    pdf_show_watermark BOOLEAN,
    pdf_header_text TEXT,
    pdf_footer_text TEXT,
    default_proposal_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Popular com dados iniciais do .env
INSERT INTO public.settings (
    id, 
    company_name,
    trade_name, 
    cnpj, 
    email,
    phones,
    street_address,
    neighborhood,
    city,
    state,
    postal_code,
    bank_name,
    bank_agency,
    bank_account,
    pix_key,
    mission,
    vision,
    values
)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'JSP Automação Industrial & Solar',
    'JSP Elétrica',
    '41.280.764/0001-65',
    'atendimento@eletricasaroba.com',
    ARRAY['(15) 99670-2036', '(15) 99802-5861'],
    'Rua Indalécio Costa, 890 – Barra Funda',
    'Tietê',
    'Tietê',
    'SP',
    '18530-170',
    'CORA SCFI 403',
    '0001',
    '4633457-0',
    'atendimento@eletricasaroba.com',
    'Fornecer soluções completas em automação industrial e energia solar, agregando valor ao negócio dos nossos clientes.',
    'Ser referência em automação industrial e energia renovável no Rio Grande do Sul até 2027.',
    ARRAY['Qualidade', 'Comprometimento', 'Inovação', 'Sustentabilidade', 'Ética']
)
ON CONFLICT (id) DO NOTHING;

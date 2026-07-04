BEGIN;

CREATE TABLE core.alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 001_baseline

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE core.users (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    name VARCHAR(150) NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    password_hash VARCHAR NOT NULL, 
    role VARCHAR(50) NOT NULL, 
    is_active BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT users_pkey PRIMARY KEY (id), 
    CONSTRAINT users_email_key UNIQUE (email), 
    CONSTRAINT check_user_role CHECK (role IN ('admin', 'user', 'technician', 'finance'))
);

COMMENT ON TABLE core.users IS 'Tabela de usußrios do sistema com autenticaþÒo';

COMMENT ON COLUMN core.users.password_hash IS 'Hash bcrypt da senha (nunca expor em APIs)';

COMMENT ON COLUMN core.users.role IS 'Papel do usußrio: admin, user, technician, finance';

COMMENT ON COLUMN core.users.is_active IS 'Flag de ativaþÒo (soft delete)';

CREATE TABLE core.orders (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    description TEXT NOT NULL, 
    total NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    CONSTRAINT orders_pkey PRIMARY KEY (id), 
    CONSTRAINT orders_user_id_fkey FOREIGN KEY(user_id) REFERENCES core.users (id) ON DELETE CASCADE
);

CREATE INDEX ix_core_orders_user_id ON core.orders (user_id);

COMMENT ON TABLE core.orders IS 'Tabela de pedidos/ordens do sistema';

COMMENT ON COLUMN core.orders.user_id IS 'FK para usußrio dono do pedido (multi-tenant)';

COMMENT ON COLUMN core.orders.total IS 'Valor total do pedido';

CREATE TABLE core.financial_entries (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    order_id UUID, 
    user_id UUID NOT NULL, 
    kind VARCHAR(20) NOT NULL, 
    status VARCHAR(20) DEFAULT 'pending' NOT NULL, 
    amount NUMERIC(12, 2) NOT NULL, 
    description TEXT NOT NULL, 
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    CONSTRAINT financial_entries_pkey PRIMARY KEY (id), 
    CONSTRAINT financial_entries_order_id_fkey FOREIGN KEY(order_id) REFERENCES core.orders (id) ON DELETE SET NULL, 
    CONSTRAINT financial_entries_user_id_fkey FOREIGN KEY(user_id) REFERENCES core.users (id) ON DELETE CASCADE, 
    CONSTRAINT unique_order_entry UNIQUE (order_id), 
    CONSTRAINT check_financial_kind CHECK (kind IN ('revenue', 'expense')), 
    CONSTRAINT check_financial_status CHECK (status IN ('pending', 'paid', 'canceled')), 
    CONSTRAINT check_financial_amount_positive CHECK (amount >= 0)
);

CREATE INDEX idx_financial_entries_user_occurred
        ON core.financial_entries (user_id, occurred_at DESC);

CREATE INDEX idx_financial_entries_status ON core.financial_entries (status);

CREATE INDEX idx_financial_entries_kind ON core.financial_entries (kind);

CREATE INDEX idx_financial_entries_order 
        ON core.financial_entries(order_id) 
        WHERE order_id IS NOT NULL;

COMMENT ON TABLE core.financial_entries IS 'Lanþamentos financeiros (receitas/despesas) com integraþÒo automßtica de pedidos';

COMMENT ON COLUMN core.financial_entries.order_id IS 'FK para order (NULL se lanþamento manual)';

COMMENT ON COLUMN core.financial_entries.kind IS 'Tipo: revenue (receita) ou expense (despesa)';

COMMENT ON COLUMN core.financial_entries.status IS 'Status: pending, paid, canceled';

COMMENT ON COLUMN core.financial_entries.occurred_at IS 'Data de ocorrÛncia do lanþamento';

COMMENT ON CONSTRAINT unique_order_entry ON core.financial_entries IS 'Garante um ·nico lanþamento automßtico por pedido';

COMMENT ON INDEX core.idx_financial_entries_user_occurred IS 'Otimiza consultas multi-tenant ordenadas por data';

COMMENT ON INDEX core.idx_financial_entries_status IS 'Otimiza filtros por status (pending, paid, canceled)';

COMMENT ON INDEX core.idx_financial_entries_order IS 'Partial index para lanþamentos vinculados a pedidos';

COMMENT ON INDEX core.idx_financial_entries_kind IS 'Otimiza filtros por tipo (revenue/expense)';

INSERT INTO core.alembic_version (version_num) VALUES ('001_baseline') RETURNING core.alembic_version.version_num;

-- Running upgrade 001_baseline -> 002_add_orders_updated_at

ALTER TABLE core.orders ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();

UPDATE core.orders
        SET updated_at = created_at
        WHERE updated_at IS NULL;

ALTER TABLE core.orders ALTER COLUMN updated_at SET NOT NULL;

UPDATE core.alembic_version SET version_num='002_add_orders_updated_at' WHERE core.alembic_version.version_num = '001_baseline';

-- Running upgrade 001_baseline -> 002_audit_logs

CREATE TABLE core.audit_logs (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    action VARCHAR(20) NOT NULL, 
    entity_type VARCHAR(50) NOT NULL, 
    entity_id UUID NOT NULL, 
    before JSONB, 
    after JSONB, 
    request_id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT audit_logs_pkey PRIMARY KEY (id), 
    CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY(user_id) REFERENCES core.users (id) ON DELETE CASCADE, 
    CONSTRAINT check_audit_action CHECK (action IN ('create', 'update', 'delete')), 
    CONSTRAINT check_audit_entity_type CHECK (entity_type IN ('order', 'financial_entry', 'user'))
);

CREATE INDEX ix_audit_logs_user_id ON core.audit_logs (user_id);

CREATE INDEX ix_audit_logs_entity ON core.audit_logs (entity_type, entity_id);

CREATE INDEX ix_audit_logs_created_at ON core.audit_logs (created_at DESC);

CREATE INDEX ix_audit_logs_request_id ON core.audit_logs (request_id);

COMMENT ON TABLE core.audit_logs IS 'Registro de auditoria de todas operaþ§es crÝticas do sistema';

COMMENT ON COLUMN core.audit_logs.user_id IS 'Usußrio que executou a aþÒo';

COMMENT ON COLUMN core.audit_logs.action IS 'Tipo de operaþÒo: create, update, delete';

COMMENT ON COLUMN core.audit_logs.entity_type IS 'Tipo de entidade: order, financial_entry, user';

COMMENT ON COLUMN core.audit_logs.entity_id IS 'ID da entidade afetada';

COMMENT ON COLUMN core.audit_logs.before IS 'Estado anterior da entidade (NULL em create)';

COMMENT ON COLUMN core.audit_logs.after IS 'Estado atual da entidade (NULL em delete)';

COMMENT ON COLUMN core.audit_logs.request_id IS 'X-Request-ID do middleware para correlaþÒo';

COMMENT ON COLUMN core.audit_logs.created_at IS 'Timestamp da operaþÒo';

INSERT INTO core.alembic_version (version_num) VALUES ('002_audit_logs') RETURNING core.alembic_version.version_num;

-- Running upgrade 002_audit_logs, 002_add_orders_updated_at -> 003

ALTER TABLE core.orders ADD COLUMN deleted_at TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE core.orders ADD COLUMN deleted_by UUID;

ALTER TABLE core.orders ADD CONSTRAINT fk_orders_deleted_by_users FOREIGN KEY(deleted_by) REFERENCES core.users (id) ON DELETE SET NULL;

CREATE INDEX ix_orders_deleted_at ON core.orders (deleted_at);

ALTER TABLE core.financial_entries ADD COLUMN deleted_at TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE core.financial_entries ADD COLUMN deleted_by UUID;

ALTER TABLE core.financial_entries ADD CONSTRAINT fk_financial_entries_deleted_by_users FOREIGN KEY(deleted_by) REFERENCES core.users (id) ON DELETE SET NULL;

CREATE INDEX ix_financial_entries_deleted_at ON core.financial_entries (deleted_at);

COMMENT ON COLUMN core.orders.deleted_at IS 'Timestamp de quando o registro foi soft-deleted (NULL = ativo)';

COMMENT ON COLUMN core.orders.deleted_by IS 'ID do usußrio que deletou o registro';

COMMENT ON COLUMN core.financial_entries.deleted_at IS 'Timestamp de quando o registro foi soft-deleted (NULL = ativo)';

COMMENT ON COLUMN core.financial_entries.deleted_by IS 'ID do usußrio que deletou o registro';

DELETE FROM core.alembic_version WHERE core.alembic_version.version_num = '002_audit_logs';

UPDATE core.alembic_version SET version_num='003' WHERE core.alembic_version.version_num = '002_add_orders_updated_at';

-- Running upgrade 003 -> 004_add_rbac

CREATE TABLE core.roles (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    name VARCHAR(50) NOT NULL, 
    description VARCHAR(255), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT roles_pkey PRIMARY KEY (id), 
    CONSTRAINT roles_name_key UNIQUE (name)
);

CREATE TABLE core.permissions (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    resource VARCHAR(100) NOT NULL, 
    action VARCHAR(50) NOT NULL, 
    description VARCHAR(255), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT permissions_pkey PRIMARY KEY (id), 
    CONSTRAINT permissions_resource_action_key UNIQUE (resource, action)
);

CREATE TABLE core.user_roles (
    user_id UUID NOT NULL, 
    role_id UUID NOT NULL, 
    assigned_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id), 
    CONSTRAINT user_roles_user_id_fkey FOREIGN KEY(user_id) REFERENCES core.users (id) ON DELETE CASCADE, 
    CONSTRAINT user_roles_role_id_fkey FOREIGN KEY(role_id) REFERENCES core.roles (id) ON DELETE CASCADE
);

CREATE TABLE core.role_permissions (
    role_id UUID NOT NULL, 
    permission_id UUID NOT NULL, 
    assigned_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id), 
    CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY(role_id) REFERENCES core.roles (id) ON DELETE CASCADE, 
    CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY(permission_id) REFERENCES core.permissions (id) ON DELETE CASCADE
);

CREATE INDEX idx_user_roles_user_id ON core.user_roles (user_id);

CREATE INDEX idx_user_roles_role_id ON core.user_roles (role_id);

CREATE INDEX idx_role_permissions_role_id ON core.role_permissions (role_id);

CREATE INDEX idx_role_permissions_permission_id ON core.role_permissions (permission_id);

CREATE UNIQUE INDEX idx_permissions_resource_action ON core.permissions (resource, action);

UPDATE core.alembic_version SET version_num='004_add_rbac' WHERE core.alembic_version.version_num = '003';

-- Running upgrade 004_add_rbac -> 005_rbac_idempotent

CREATE TABLE IF NOT EXISTS core.roles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT now()
        );

CREATE TABLE IF NOT EXISTS core.permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            resource VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT permissions_resource_action_key UNIQUE (resource, action)
        );

CREATE TABLE IF NOT EXISTS core.user_roles (
            user_id UUID NOT NULL,
            role_id UUID NOT NULL,
            assigned_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, role_id),
            CONSTRAINT user_roles_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE CASCADE,
            CONSTRAINT user_roles_role_id_fkey 
                FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE
        );

CREATE TABLE IF NOT EXISTS core.role_permissions (
            role_id UUID NOT NULL,
            permission_id UUID NOT NULL,
            assigned_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (role_id, permission_id),
            CONSTRAINT role_permissions_role_id_fkey 
                FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE,
            CONSTRAINT role_permissions_permission_id_fkey 
                FOREIGN KEY (permission_id) REFERENCES core.permissions(id) ON DELETE CASCADE
        );

CREATE INDEX IF NOT EXISTS idx_user_roles_user_id 
        ON core.user_roles(user_id);

CREATE INDEX IF NOT EXISTS idx_user_roles_role_id 
        ON core.user_roles(role_id);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id 
        ON core.role_permissions(role_id);

CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id 
        ON core.role_permissions(permission_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_permissions_resource_action 
        ON core.permissions(resource, action);

UPDATE core.alembic_version SET version_num='005_rbac_idempotent' WHERE core.alembic_version.version_num = '004_add_rbac';

-- Running upgrade 005_rbac_idempotent -> 006_add_customers

CREATE TABLE core.customers (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    cpf_cnpj VARCHAR(14), 
    email VARCHAR(120), 
    phone VARCHAR(15), 
    cep VARCHAR(8), 
    street VARCHAR(200), 
    number VARCHAR(20), 
    neighborhood VARCHAR(100), 
    city VARCHAR(100), 
    state VARCHAR(2), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_core_customers_name ON core.customers (name);

CREATE INDEX ix_core_customers_cpf_cnpj ON core.customers (cpf_cnpj);

CREATE INDEX ix_core_customers_deleted_at ON core.customers (deleted_at);

CREATE UNIQUE INDEX ix_core_customers_cpf_cnpj_unique 
        ON core.customers (cpf_cnpj) 
        WHERE deleted_at IS NULL AND cpf_cnpj IS NOT NULL;

UPDATE core.alembic_version SET version_num='006_add_customers' WHERE core.alembic_version.version_num = '005_rbac_idempotent';

-- Running upgrade 006_add_customers -> 007_enhance_customers

ALTER TABLE core.customers ADD COLUMN person_type VARCHAR(2) DEFAULT 'PF';

ALTER TABLE core.customers ADD COLUMN trade_name VARCHAR(120);

ALTER TABLE core.customers ADD COLUMN state_registration VARCHAR(20);

ALTER TABLE core.customers ADD COLUMN phone2 VARCHAR(15);

ALTER TABLE core.customers ADD COLUMN address_complement VARCHAR(100);

ALTER TABLE core.customers ADD COLUMN notes TEXT;

ALTER TABLE core.customers ADD COLUMN status VARCHAR(10) DEFAULT 'active' NOT NULL;

UPDATE core.alembic_version SET version_num='007_enhance_customers' WHERE core.alembic_version.version_num = '006_add_customers';

-- Running upgrade 007_enhance_customers -> 008_add_products

CREATE TABLE core.products (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    code VARCHAR(50), 
    name VARCHAR(200) NOT NULL, 
    category VARCHAR(80), 
    unit VARCHAR(20), 
    description TEXT, 
    cost_price NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
    sale_price NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
    stock_qty NUMERIC(12, 3) DEFAULT 0 NOT NULL, 
    stock_min NUMERIC(12, 3) DEFAULT 0 NOT NULL, 
    active BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    deleted_at TIMESTAMP WITHOUT TIME ZONE, 
    deleted_by UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES core.users (id) ON DELETE CASCADE, 
    FOREIGN KEY(deleted_by) REFERENCES core.users (id) ON DELETE SET NULL, 
    CONSTRAINT check_product_cost_price_positive CHECK (cost_price >= 0), 
    CONSTRAINT check_product_sale_price_positive CHECK (sale_price >= 0), 
    CONSTRAINT check_product_stock_qty_positive CHECK (stock_qty >= 0), 
    CONSTRAINT check_product_stock_min_positive CHECK (stock_min >= 0)
);

CREATE INDEX idx_products_user_id ON core.products (user_id);

CREATE INDEX idx_products_name ON core.products (name);

CREATE INDEX idx_products_code ON core.products (code);

CREATE INDEX idx_products_category ON core.products (category);

CREATE INDEX idx_products_active ON core.products (active);

CREATE INDEX idx_products_deleted_at ON core.products (deleted_at);

CREATE INDEX idx_products_user_category ON core.products (user_id, category);

CREATE INDEX idx_products_user_active ON core.products (user_id, active);

UPDATE core.alembic_version SET version_num='008_add_products' WHERE core.alembic_version.version_num = '007_enhance_customers';

-- Running upgrade 008_add_products -> 009_extend_products

ALTER TABLE core.products ADD COLUMN codigo_barras VARCHAR(50);

ALTER TABLE core.products ADD COLUMN marca VARCHAR(100);

ALTER TABLE core.products ADD COLUMN modelo VARCHAR(100);

ALTER TABLE core.products ADD COLUMN subcategoria VARCHAR(80);

ALTER TABLE core.products ADD COLUMN peso NUMERIC(10, 3);

ALTER TABLE core.products ADD COLUMN dimensoes VARCHAR(100);

ALTER TABLE core.products ADD COLUMN markup NUMERIC(5, 2);

ALTER TABLE core.products ADD COLUMN margem_lucro NUMERIC(5, 2);

ALTER TABLE core.products ADD COLUMN estoque_maximo NUMERIC(12, 3);

ALTER TABLE core.products ADD COLUMN controla_estoque BOOLEAN DEFAULT true NOT NULL;

ALTER TABLE core.products ADD COLUMN fornecedor_id UUID;

ALTER TABLE core.products ADD COLUMN observacoes TEXT;

CREATE UNIQUE INDEX idx_products_codigo_barras_unique 
        ON core.products (codigo_barras) 
        WHERE codigo_barras IS NOT NULL AND deleted_at IS NULL;

CREATE INDEX idx_products_marca ON core.products (marca);

CREATE INDEX idx_products_subcategoria ON core.products (subcategoria);

CREATE INDEX idx_products_user_subcategoria ON core.products (user_id, subcategoria);

ALTER TABLE core.products ADD CONSTRAINT check_product_peso_positive CHECK (peso IS NULL OR peso >= 0);

ALTER TABLE core.products ADD CONSTRAINT check_product_markup_valid CHECK (markup IS NULL OR (markup >= 0 AND markup <= 1000));

ALTER TABLE core.products ADD CONSTRAINT check_product_margem_lucro_valid CHECK (margem_lucro IS NULL OR (margem_lucro >= -100 AND margem_lucro <= 1000));

ALTER TABLE core.products ADD CONSTRAINT check_product_estoque_maximo_positive CHECK (estoque_maximo IS NULL OR estoque_maximo >= 0);

UPDATE core.alembic_version SET version_num='009_extend_products' WHERE core.alembic_version.version_num = '008_add_products';

-- Running upgrade 009_extend_products -> 010_create_suppliers

CREATE TABLE core.suppliers (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    nome VARCHAR(150) NOT NULL, 
    nome_fantasia VARCHAR(150), 
    tipo VARCHAR(2) NOT NULL, 
    cnpj_cpf VARCHAR(20) NOT NULL, 
    rg_ie VARCHAR(20), 
    inscricao_estadual VARCHAR(20), 
    inscricao_municipal VARCHAR(20), 
    im VARCHAR(20), 
    email VARCHAR(150), 
    email_financeiro VARCHAR(150), 
    telefone VARCHAR(20), 
    celular VARCHAR(20), 
    whatsapp VARCHAR(20), 
    site VARCHAR(200), 
    website VARCHAR(200), 
    contato_nome VARCHAR(100), 
    contato_cargo VARCHAR(100), 
    contato_email VARCHAR(150), 
    contato_telefone VARCHAR(20), 
    cep VARCHAR(10), 
    endereco VARCHAR(200), 
    numero VARCHAR(20), 
    complemento VARCHAR(100), 
    bairro VARCHAR(100), 
    cidade VARCHAR(100), 
    estado VARCHAR(2), 
    pais VARCHAR(50), 
    segmento VARCHAR(100), 
    porte_empresa VARCHAR(20), 
    origem VARCHAR(50), 
    classificacao VARCHAR(50), 
    categoria VARCHAR(50), 
    categoria_fiscal VARCHAR(50), 
    condicoes_pagamento VARCHAR(100), 
    prazo_entrega VARCHAR(50), 
    forma_entrega VARCHAR(50), 
    tempo_entrega_medio VARCHAR(50), 
    limite_credito NUMERIC(15, 2), 
    prazo_pagamento_padrao INTEGER, 
    desconto_padrao NUMERIC(5, 2), 
    data_nascimento DATE, 
    data_fundacao DATE, 
    genero VARCHAR(20), 
    estado_civil VARCHAR(20), 
    profissao VARCHAR(100), 
    certificacoes TEXT, 
    banco_principal VARCHAR(100), 
    agencia VARCHAR(20), 
    conta VARCHAR(30), 
    pix VARCHAR(100), 
    observacoes TEXT, 
    observacoes_internas TEXT, 
    status VARCHAR(20), 
    motivo_bloqueio VARCHAR(200), 
    ativo BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES core.users (id) ON DELETE CASCADE, 
    UNIQUE (cnpj_cpf)
);

COMMENT ON COLUMN core.suppliers.nome IS 'RazÒo Social (PJ) ou Nome Completo (PF)';

COMMENT ON COLUMN core.suppliers.nome_fantasia IS 'Nome Fantasia da empresa';

COMMENT ON COLUMN core.suppliers.tipo IS 'PF (Pessoa FÝsica) ou PJ (Pessoa JurÝdica)';

COMMENT ON COLUMN core.suppliers.cnpj_cpf IS 'CPF (11 dÝgitos) ou CNPJ (14 dÝgitos)';

COMMENT ON COLUMN core.suppliers.rg_ie IS 'RG (PF) ou InscriþÒo Estadual (PJ)';

COMMENT ON COLUMN core.suppliers.inscricao_estadual IS 'InscriþÒo Estadual (PJ)';

COMMENT ON COLUMN core.suppliers.inscricao_municipal IS 'InscriþÒo Municipal (PJ)';

COMMENT ON COLUMN core.suppliers.im IS 'InscriþÒo Municipal (alternativo)';

COMMENT ON COLUMN core.suppliers.email IS 'Email principal';

COMMENT ON COLUMN core.suppliers.email_financeiro IS 'Email do setor financeiro';

COMMENT ON COLUMN core.suppliers.telefone IS 'Telefone fixo';

COMMENT ON COLUMN core.suppliers.celular IS 'Celular';

COMMENT ON COLUMN core.suppliers.whatsapp IS 'WhatsApp';

COMMENT ON COLUMN core.suppliers.site IS 'Website (alternativo)';

COMMENT ON COLUMN core.suppliers.website IS 'Website principal';

COMMENT ON COLUMN core.suppliers.contato_nome IS 'Nome do contato responsßvel';

COMMENT ON COLUMN core.suppliers.contato_cargo IS 'Cargo do contato';

COMMENT ON COLUMN core.suppliers.contato_email IS 'Email do contato';

COMMENT ON COLUMN core.suppliers.contato_telefone IS 'Telefone do contato';

COMMENT ON COLUMN core.suppliers.cep IS 'CEP (8 dÝgitos)';

COMMENT ON COLUMN core.suppliers.endereco IS 'Logradouro (Rua, Avenida, etc)';

COMMENT ON COLUMN core.suppliers.numero IS 'N·mero do im¾vel';

COMMENT ON COLUMN core.suppliers.complemento IS 'Complemento (Apt, Sala, etc)';

COMMENT ON COLUMN core.suppliers.bairro IS 'Bairro';

COMMENT ON COLUMN core.suppliers.cidade IS 'Cidade';

COMMENT ON COLUMN core.suppliers.estado IS 'UF (sigla do estado)';

COMMENT ON COLUMN core.suppliers.pais IS 'PaÝs';

COMMENT ON COLUMN core.suppliers.segmento IS 'Segmento de atuaþÒo (ex: Tecnologia, ComÚrcio)';

COMMENT ON COLUMN core.suppliers.porte_empresa IS 'MEI, Micro, Pequena, MÚdia, Grande';

COMMENT ON COLUMN core.suppliers.origem IS 'Como nos conheceu (IndicaþÒo, Google, etc)';

COMMENT ON COLUMN core.suppliers.classificacao IS 'Classe A/B/C/D - Premium/Bom/Regular/AtenþÒo';

COMMENT ON COLUMN core.suppliers.categoria IS 'Categoria comercial (Equipamentos, Serviþos, etc)';

COMMENT ON COLUMN core.suppliers.categoria_fiscal IS 'Categoria fiscal';

COMMENT ON COLUMN core.suppliers.condicoes_pagamento IS 'Ex: 30/60 dias, └ vista';

COMMENT ON COLUMN core.suppliers.prazo_entrega IS 'Ex: 5-10 dias ·teis';

COMMENT ON COLUMN core.suppliers.forma_entrega IS 'Ex: FOB, CIF, Transportadora';

COMMENT ON COLUMN core.suppliers.tempo_entrega_medio IS 'Tempo mÚdio de entrega';

COMMENT ON COLUMN core.suppliers.limite_credito IS 'Limite de crÚdito aprovado';

COMMENT ON COLUMN core.suppliers.prazo_pagamento_padrao IS 'Prazo padrÒo em dias';

COMMENT ON COLUMN core.suppliers.desconto_padrao IS 'Desconto padrÒo em %';

COMMENT ON COLUMN core.suppliers.data_nascimento IS 'Data de nascimento (PF)';

COMMENT ON COLUMN core.suppliers.data_fundacao IS 'Data de fundaþÒo (PJ)';

COMMENT ON COLUMN core.suppliers.genero IS 'Masculino, Feminino, Outros';

COMMENT ON COLUMN core.suppliers.estado_civil IS 'Solteiro, Casado, Divorciado, Vi·vo';

COMMENT ON COLUMN core.suppliers.profissao IS 'ProfissÒo (PF)';

COMMENT ON COLUMN core.suppliers.certificacoes IS 'Certificaþ§es da empresa';

COMMENT ON COLUMN core.suppliers.banco_principal IS 'Nome do banco principal';

COMMENT ON COLUMN core.suppliers.agencia IS 'AgÛncia bancßria';

COMMENT ON COLUMN core.suppliers.conta IS 'Conta bancßria';

COMMENT ON COLUMN core.suppliers.pix IS 'Chave PIX (CPF/CNPJ/Email/Telefone/Aleat¾ria)';

COMMENT ON COLUMN core.suppliers.observacoes IS 'Observaþ§es gerais (visÝvel)';

COMMENT ON COLUMN core.suppliers.observacoes_internas IS 'Observaþ§es internas (nÒo visÝvel ao fornecedor)';

COMMENT ON COLUMN core.suppliers.status IS 'Ativo, Inativo, Bloqueado';

COMMENT ON COLUMN core.suppliers.motivo_bloqueio IS 'Motivo do bloqueio (se aplicßvel)';

COMMENT ON COLUMN core.suppliers.ativo IS 'Soft delete';

CREATE UNIQUE INDEX ix_suppliers_user_documento ON core.suppliers (user_id, cnpj_cpf);

CREATE INDEX ix_suppliers_nome ON core.suppliers (nome);

CREATE INDEX ix_suppliers_nome_fantasia ON core.suppliers (nome_fantasia);

CREATE INDEX ix_suppliers_tipo ON core.suppliers (tipo);

CREATE INDEX ix_suppliers_categoria ON core.suppliers (categoria);

CREATE INDEX ix_suppliers_classificacao ON core.suppliers (classificacao);

CREATE INDEX ix_suppliers_email ON core.suppliers (email);

CREATE INDEX ix_suppliers_ativo ON core.suppliers (ativo);

CREATE INDEX ix_suppliers_user_ativo ON core.suppliers (user_id, ativo);

CREATE INDEX ix_suppliers_cidade_estado ON core.suppliers (cidade, estado);

ALTER TABLE core.suppliers ADD CONSTRAINT ck_suppliers_tipo CHECK (tipo IN ('PF', 'PJ'));

ALTER TABLE core.suppliers ADD CONSTRAINT ck_suppliers_limite_credito CHECK (limite_credito >= 0);

ALTER TABLE core.suppliers ADD CONSTRAINT ck_suppliers_desconto_padrao CHECK (desconto_padrao >= 0 AND desconto_padrao <= 100);

ALTER TABLE core.suppliers ADD CONSTRAINT ck_suppliers_prazo_pagamento CHECK (prazo_pagamento_padrao >= 0);

ALTER TABLE core.suppliers ADD CONSTRAINT ck_suppliers_estado_length CHECK (estado IS NULL OR LENGTH(estado) = 2);

UPDATE core.alembic_version SET version_num='010_create_suppliers' WHERE core.alembic_version.version_num = '009_extend_products';

COMMIT;


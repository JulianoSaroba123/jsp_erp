-- Script de correção rápida para criar tabelas faltantes
-- Baseado nas migrations do Alembic 

-- Tabela de Customers
CREATE TABLE IF NOT EXISTS core.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    document VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    postal_code VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Tabela de Products
CREATE TABLE IF NOT EXISTS core.products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    unit_price NUMERIC(12, 2) DEFAULT 0,
    cost_price NUMERIC(12, 2),
    stock_quantity INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Tabela de Suppliers
CREATE TABLE IF NOT EXISTS core.suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    document VARCHAR(20),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    postal_code VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Tabela de Service Orders
CREATE TABLE IF NOT EXISTS core.service_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID REFERENCES core.customers(id),
    user_id UUID NOT NULL REFERENCES core.users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pendente',
    priority VARCHAR(20) DEFAULT 'media',
    scheduled_date DATE,
    completed_date DATE,
    total_amount NUMERIC(12, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES core.users(id)
);

-- Tabela de Proposals
CREATE TABLE IF NOT EXISTS core.proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES core.customers(id),
    customer_contact VARCHAR(200),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    observations TEXT,
    service_amount NUMERIC(12, 2) DEFAULT 0,
    product_amount NUMERIC(12, 2) DEFAULT 0,
    total_amount NUMERIC(12, 2) DEFAULT 0,
    discount NUMERIC(12, 2) DEFAULT 0,
    final_amount NUMERIC(12, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'rascunho',
    valid_until DATE,
    user_id UUID REFERENCES core.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES core.users(id)
);

-- Tabela de Proposal Items
CREATE TABLE IF NOT EXISTS core.proposal_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES core.proposals(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    service_type VARCHAR(20) NOT NULL,
    quantity NUMERIC(10, 3) NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    total_price NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de Proposal Products
CREATE TABLE IF NOT EXISTS core.proposal_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES core.proposals(id) ON DELETE CASCADE,
    product_id UUID REFERENCES core.products(id),
    description TEXT NOT NULL,
    quantity NUMERIC(10, 3) NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    total_price NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de Audit Logs
CREATE TABLE IF NOT EXISTS core.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES core.users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Criar índices essenciais
CREATE INDEX IF NOT EXISTS idx_customers_name ON core.customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_email ON core.customers(email);
CREATE INDEX IF NOT EXISTS idx_products_code ON core.products(code);
CREATE INDEX IF NOT EXISTS idx_products_name ON core.products(name);
CREATE INDEX IF NOT EXISTS idx_products_category ON core.products(category);
CREATE INDEX IF NOT EXISTS idx_service_orders_customer_id ON core.service_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_service_orders_user_id ON core.service_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_service_orders_status ON core.service_orders(status);
CREATE INDEX IF NOT EXISTS idx_service_orders_number ON core.service_orders(number);
CREATE INDEX IF NOT EXISTS idx_proposals_customer_id ON core.proposals(customer_id);
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON core.proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON core.proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_number ON core.proposals(number);
CREATE INDEX IF NOT EXISTS idx_proposal_items_proposal_id ON core.proposal_items(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_products_proposal_id ON core.proposal_products(proposal_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON core.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON core.audit_logs(resource_type, resource_id);

-- Mensagem de sucesso
SELECT '✅ Tabelas criadas com sucesso!' as status;

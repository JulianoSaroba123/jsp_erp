-- Migration 008: Create core.products table
-- Manually extracted from 008_add_products.py alembic migration

-- Drop if exists (idempotent)
DROP TABLE IF EXISTS core.products CASCADE;

-- Create products table
CREATE TABLE core.products (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    code VARCHAR(50),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(80),
    unit VARCHAR(20),
    description TEXT,
    cost_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    sale_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    stock_qty NUMERIC(12, 3) NOT NULL DEFAULT 0,
    stock_min NUMERIC(12, 3) NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    deleted_by UUID,
    
    CONSTRAINT pk_products PRIMARY KEY (id),
    CONSTRAINT fk_products_user_id FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_products_deleted_by FOREIGN KEY (deleted_by) REFERENCES core.users(id) ON DELETE SET NULL,
    CONSTRAINT check_product_cost_price_positive CHECK (cost_price >= 0),
    CONSTRAINT check_product_sale_price_positive CHECK (sale_price >= 0),
    CONSTRAINT check_product_stock_qty_positive CHECK (stock_qty >= 0),
    CONSTRAINT check_product_stock_min_positive CHECK (stock_min >= 0)
);

-- Create indexes
CREATE INDEX idx_products_user_id ON core.products(user_id);
CREATE INDEX idx_products_name ON core.products(name);
CREATE INDEX idx_products_code ON core.products(code);
CREATE INDEX idx_products_category ON core.products(category);
CREATE INDEX idx_products_active ON core.products(active);
CREATE INDEX idx_products_deleted_at ON core.products(deleted_at);
CREATE INDEX idx_products_user_category ON core.products(user_id, category);
CREATE INDEX idx_products_user_active ON core.products(user_id, active);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON core.products TO jsp_user;

COMMENT ON TABLE core.products IS 'Tabela de produtos - Migration 008';

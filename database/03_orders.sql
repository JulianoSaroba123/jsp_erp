-- =====================================
-- TABELA ORDERS
-- =====================================
CREATE TABLE IF NOT EXISTS core.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

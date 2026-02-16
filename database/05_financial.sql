-- =====================================
-- 05 - FINANCIAL ENTRIES
-- Lançamentos financeiros (receitas/despesas)
-- Integração automática com Orders
-- =====================================

-- Tabela de lançamentos financeiros
CREATE TABLE IF NOT EXISTS core.financial_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES core.orders(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('revenue', 'expense')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'canceled')),
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    description TEXT NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraint de não duplicidade: um lançamento automático por pedido
    -- order_id pode ser NULL (lançamento manual), mas se existir deve ser único
    CONSTRAINT unique_order_entry UNIQUE (order_id)
);

-- Comentários explicativos
COMMENT ON TABLE core.financial_entries IS 'Lançamentos financeiros (receitas/despesas) com integração automática de pedidos';
COMMENT ON COLUMN core.financial_entries.order_id IS 'FK para order (NULL se lançamento manual)';
COMMENT ON COLUMN core.financial_entries.kind IS 'Tipo: revenue (receita) ou expense (despesa)';
COMMENT ON COLUMN core.financial_entries.status IS 'Status: pending, paid, canceled';
COMMENT ON COLUMN core.financial_entries.occurred_at IS 'Data de ocorrência do lançamento';
COMMENT ON CONSTRAINT unique_order_entry ON core.financial_entries IS 'Garante um único lançamento automático por pedido';

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_financial_entries_user_occurred 
    ON core.financial_entries(user_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_financial_entries_status 
    ON core.financial_entries(status);

CREATE INDEX IF NOT EXISTS idx_financial_entries_order 
    ON core.financial_entries(order_id) 
    WHERE order_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_financial_entries_kind 
    ON core.financial_entries(kind);

-- Comentários nos índices
COMMENT ON INDEX idx_financial_entries_user_occurred IS 'Otimiza consultas multi-tenant ordenadas por data';
COMMENT ON INDEX idx_financial_entries_status IS 'Otimiza filtros por status (pending, paid, canceled)';
COMMENT ON INDEX idx_financial_entries_order IS 'Partial index para lançamentos vinculados a pedidos';
COMMENT ON INDEX idx_financial_entries_kind IS 'Otimiza filtros por tipo (revenue/expense)';

-- Validação básica de instalação
DO $$
BEGIN
    RAISE NOTICE '✅ Tabela core.financial_entries criada com sucesso';
    RAISE NOTICE '   - Constraint UNIQUE(order_id) para evitar duplicidade';
    RAISE NOTICE '   - Índices de performance criados';
    RAISE NOTICE '   - Multi-tenant via user_id';
END $$;

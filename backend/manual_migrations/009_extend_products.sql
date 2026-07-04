-- Migration 009: Extend products table with advanced fields
-- Manually extracted from 009_extend_products.py alembic migration

-- Add extended identification fields
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS codigo_barras VARCHAR(50);
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS marca VARCHAR(100);
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS modelo VARCHAR(100);
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS subcategoria VARCHAR(80);

-- Add physical characteristics
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS peso NUMERIC(10, 3);
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS dimensoes VARCHAR(100);

-- Add price management
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS markup NUMERIC(5, 2);
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS margem_lucro NUMERIC(5, 2);

-- Add stock management
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS estoque_maximo NUMERIC(12, 3);
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS controla_estoque BOOLEAN NOT NULL DEFAULT true;

-- Add relationships
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS fornecedor_id UUID;

-- Add observations
ALTER TABLE core.products ADD COLUMN IF NOT EXISTS observacoes TEXT;

-- Create unique index for barcode (only non-deleted items)
DROP INDEX IF EXISTS core.idx_products_codigo_barras_unique;
CREATE UNIQUE INDEX idx_products_codigo_barras_unique 
    ON core.products (codigo_barras) 
    WHERE codigo_barras IS NOT NULL AND deleted_at IS NULL;

COMMENT ON COLUMN core.products.codigo_barras IS 'Código de barras único do produto';
COMMENT ON COLUMN core.products.fornecedor_id IS 'FK para fornecedores (será linkada quando tabela suppliers for criada)';

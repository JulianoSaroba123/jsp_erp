-- =====================================
-- 04 - AUTH SETUP (idempotente)
-- Configurações adicionais para autenticação
-- =====================================

-- A tabela core.users já existe em 01_structure.sql
-- Este script apenas adiciona constraints e índices adicionais se necessário

-- Garantir que role seja válido (expandir conforme necessário)
DO $$
BEGIN
    -- Remover constraint antiga se existir (para permitir adicionar novos roles)
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_role_check'
    ) THEN
        ALTER TABLE core.users DROP CONSTRAINT users_role_check;
    END IF;
    
    -- Adicionar constraint atualizado com roles suportados
    ALTER TABLE core.users
    ADD CONSTRAINT users_role_check
    CHECK (role IN ('admin', 'user', 'technician', 'finance'));
    
EXCEPTION
    WHEN duplicate_object THEN
        -- Constraint já existe, ignorar
        NULL;
END $$;

-- Índice para otimizar busca por email (se não existir)
CREATE INDEX IF NOT EXISTS idx_users_email ON core.users (email);

-- Índice para otimizar busca por role
CREATE INDEX IF NOT EXISTS idx_users_role ON core.users (role);

-- Índice para filtrar usuários ativos
CREATE INDEX IF NOT EXISTS idx_users_is_active ON core.users (is_active);

-- Comentários úteis
COMMENT ON TABLE core.users IS 'Usuários do sistema ERP com autenticação';
COMMENT ON COLUMN core.users.role IS 'Papéis suportados: admin, user, technician, finance';
COMMENT ON COLUMN core.users.is_active IS 'Usuários inativos não podem fazer login';

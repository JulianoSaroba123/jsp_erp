-- =====================================
-- 04 - TABELA USERS (idempotente)
-- Tabela de usuários (ERP multiusuário)
-- =====================================

-- Extensão necessária para UUID
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Schema core
CREATE SCHEMA IF NOT EXISTS core;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS core.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Constraint para validar roles (idempotente)
DO $$
BEGIN
    -- Remove constraint antiga se existir (para permitir recriar)
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_role_check'
    ) THEN
        ALTER TABLE core.users DROP CONSTRAINT users_role_check;
    END IF;
    
    -- Adiciona constraint atualizado
    ALTER TABLE core.users
    ADD CONSTRAINT users_role_check
    CHECK (role IN ('admin', 'user', 'technician', 'finance'));
    
EXCEPTION
    WHEN duplicate_object THEN
        -- Já existe, ignorar
        NULL;
END $$;

-- Índices (idempotentes)
CREATE INDEX IF NOT EXISTS idx_users_email ON core.users (email);
CREATE INDEX IF NOT EXISTS idx_users_role ON core.users (role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON core.users (is_active);

-- Comentários
COMMENT ON TABLE core.users IS 'Usuários do sistema ERP com autenticação JWT';
COMMENT ON COLUMN core.users.id IS 'UUID único do usuário';
COMMENT ON COLUMN core.users.email IS 'Email único (usado para login)';
COMMENT ON COLUMN core.users.password_hash IS 'Hash bcrypt da senha (gerado via Python passlib)';
COMMENT ON COLUMN core.users.role IS 'Papel: admin (acesso total), user (padrão), technician, finance';
COMMENT ON COLUMN core.users.is_active IS 'Usuários inativos não podem fazer login';

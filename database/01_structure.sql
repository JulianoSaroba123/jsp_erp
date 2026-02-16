-- =====================================
-- 01 - EXTENSÃO
-- =====================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================
-- 02 - SCHEMA
-- =====================================
CREATE SCHEMA IF NOT EXISTS core;

-- =====================================
-- 03 - TABELA USERS
-- =====================================
CREATE TABLE IF NOT EXISTS core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- =====================================
-- 01 - EXTENSÃO
-- =====================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================
-- 02 - SCHEMA
-- =====================================
CREATE SCHEMA IF NOT EXISTS core;

-- =====================================
-- 03 - TABELA USERS
-- =====================================
CREATE TABLE IF NOT EXISTS core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- =====================================
-- 01 - EXTENSÃO
-- =====================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================
-- 02 - SCHEMA
-- =====================================
CREATE SCHEMA IF NOT EXISTS core;

-- =====================================
-- 03 - TABELA USERS
-- =====================================
CREATE TABLE IF NOT EXISTS core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- =====================================
-- SEED - USUÁRIO ADMIN
-- =====================================
INSERT INTO core.users (name, email, password_hash, role)
VALUES (
    'Juliano Saroba',
    'admin@jsp.com',
    crypt('123456', gen_salt('bf')),
    'admin'
)
ON CONFLICT (email) DO NOTHING;

-- =====================================
-- SEED - OUTROS USUÁRIOS
-- =====================================
INSERT INTO core.users (name, email, password_hash, role)
VALUES
('Tecnico 1', 'tec1@jsp.com', crypt('123456', gen_salt('bf')), 'technician'),
('Financeiro 1', 'fin@jsp.com', crypt('123456', gen_salt('bf')), 'finance')
ON CONFLICT (email) DO NOTHING;

SELECT name, email, role
FROM core.users;

SELECT name, email, role
FROM core.users
ORDER BY role;

INSERT INTO core.users (name, email, password_hash, role)
VALUES (
    'Juliano Saroba',
    'admin@jsp.com',
    crypt('123456', gen_salt('bf')),
    'admin'
)
ON CONFLICT (email) DO NOTHING;

SELECT name, email, role
FROM core.users
ORDER BY role;

CREATE TABLE core.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE core.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

SELECT * FROM core.orders;
SELECT id, name, email
FROM core.users
WHERE email = 'admin@jsp.com';

INSERT INTO core.orders (user_id, description, total)
VALUES (
  (SELECT id FROM core.users WHERE email = 'admin@jsp.com'),
  'Pedido do Admin - teste',
  250.00
);

SELECT
  o.id,
  u.name,
  u.email,
  o.description,
  o.total,
  o.created_at
FROM core.orders o
JOIN core.users u ON u.id = o.user_id
ORDER BY o.created_at DESC;



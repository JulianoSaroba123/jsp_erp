-- =========================================================
-- CORREÇÃO DE OWNERSHIP - Permitir migrations
-- =========================================================
-- Este script transfere ownership das tabelas para jsp_user
-- para que ele possa executar migrations (ALTER TABLE, etc.)
-- =========================================================

-- Conectar como postgres
\c jsp_erp_test postgres

-- Transferir ownership do schema
ALTER SCHEMA core OWNER TO jsp_user;

-- Transferir ownership das tabelas
ALTER TABLE core.users OWNER TO jsp_user;
ALTER TABLE core.orders OWNER TO jsp_user;
ALTER TABLE core.financial_entries OWNER TO jsp_user;

-- Transferir ownership de sequences (se existirem)
-- ALTER SEQUENCE core.users_id_seq OWNER TO jsp_user;
-- (não aplicável pois usamos UUID)

-- Grant all privileges
GRANT ALL ON SCHEMA core TO jsp_user;
GRANT ALL ON ALL TABLES IN SCHEMA core TO jsp_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA core TO jsp_user;

-- Configurar defaults para futuras tabelas
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT ALL ON TABLES TO jsp_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT ALL ON SEQUENCES TO jsp_user;

-- Verificação
\dt core.*
SELECT tablename, tableowner FROM pg_tables WHERE schemaname = 'core';

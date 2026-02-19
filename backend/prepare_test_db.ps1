# ==============================================================================
# Script para preparar banco de teste JSP_ERP_TEST
# Execute ANTES de rodar os testes: .\prepare_test_db.ps1
#
# IMPORTANTE: Este script configura o PostgreSQL LOCAL (nativo do Windows) que
# é o banco que os testes Python usam (localhost:5432).
# ==============================================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PREPARANDO BANCO DE TESTE (LOCAL)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Config
$DB_NAME = "jsp_erp_test"
$SUPERUSER = "postgres"

# DDL completo com soft delete
$DDL = @"
-- Remover banco existente
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME';
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME OWNER jsp_user;
"@

$DDL_SCHEMA = @"
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA core AUTHORIZATION jsp_user;
GRANT ALL ON SCHEMA core TO jsp_user;

CREATE TABLE core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE core.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES core.users(id) ON DELETE SET NULL
);

CREATE TABLE core.financial_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES core.orders(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    description TEXT,
    occurred_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES core.users(id) ON DELETE SET NULL,
    CONSTRAINT unique_order_entry UNIQUE (order_id)
);

CREATE TABLE core.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    before JSONB,
    after JSONB,
    request_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_orders_user_id ON core.orders(user_id);
CREATE INDEX ix_orders_deleted_at ON core.orders(deleted_at);
CREATE INDEX ix_financial_entries_deleted_at ON core.financial_entries(deleted_at);

-- Permissões para jsp_user
GRANT ALL ON ALL TABLES IN SCHEMA core TO jsp_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA core TO jsp_user;
"@

Write-Host "[1/3] Removendo banco de teste existente..." -ForegroundColor Yellow
psql -U $SUPERUSER -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME';" 2>$null
psql -U $SUPERUSER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>$null

Write-Host "[2/3] Criando banco de teste limpo..." -ForegroundColor Yellow
psql -U $SUPERUSER -d postgres -c "CREATE DATABASE $DB_NAME OWNER jsp_user;"

Write-Host "[3/3] Criando estrutura com soft delete..." -ForegroundColor Yellow
$DDL_SCHEMA | psql -U $SUPERUSER -d $DB_NAME

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  BANCO DE TESTE PREPARADO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Agora execute: pytest tests/" -ForegroundColor White
Write-Host "Agora execute: pytest tests/" -ForegroundColor White

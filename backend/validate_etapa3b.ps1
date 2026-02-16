#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Smoke check automatizado para ETAPA 3B (Alembic Migrations)

.DESCRIPTION
    Valida 12 checks críticos:
    - Alembic instalado e configurado
    - Schema core criado
    - 3 tabelas com constraints corretos
    - Índices de performance
    - Versionamento isolado em core

.EXAMPLE
    .\validate_etapa3b.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ETAPA 3B - SMOKE CHECK AUTOMATIZADO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$PASSED = 0
$FAILED = 0

function Test-Check {
    param(
        [string]$Name,
        [string]$Command,
        [string]$ExpectedPattern,
        [switch]$IsSQL
    )
    
    Write-Host "[$($PASSED + $FAILED + 1)] $Name..." -NoNewline
    
    try {
        if ($IsSQL) {
            # Executar SQL via psql
            $output = & psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -t -A -c $Command 2>&1
        } else {
            # Executar comando PowerShell
            $output = Invoke-Expression $Command 2>&1
        }
        
        $outputStr = $output -join "`n"
        
        if ($outputStr -match $ExpectedPattern) {
            Write-Host " ✅ PASS" -ForegroundColor Green
            $script:PASSED++
            return $true
        } else {
            Write-Host " ❌ FAIL" -ForegroundColor Red
            Write-Host "   Expected pattern: $ExpectedPattern" -ForegroundColor Yellow
            Write-Host "   Got: $outputStr" -ForegroundColor Yellow
            $script:FAILED++
            return $false
        }
    } catch {
        Write-Host " ❌ ERROR" -ForegroundColor Red
        Write-Host "   $_" -ForegroundColor Yellow
        $script:FAILED++
        return $false
    }
}

# =====================================
# Configurar conexão PostgreSQL
# =====================================
Write-Host "Configurando conexão com PostgreSQL..." -ForegroundColor Yellow

$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "❌ Arquivo .env não encontrado em: $envFile" -ForegroundColor Red
    exit 1
}

$envContent = Get-Content $envFile | Where-Object { $_ -match "^DATABASE_URL=" }
if (-not $envContent) {
    Write-Host "❌ DATABASE_URL não encontrado em .env" -ForegroundColor Red
    exit 1
}

$dbUrl = ($envContent -split "=", 2)[1]

if ($dbUrl -match "postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)") {
    $env:PGUSER = $matches[1]
    $env:PGPASSWORD = $matches[2]
    $env:PGHOST = $matches[3]
    $env:PGPORT = $matches[4]
    $env:PGDATABASE = $matches[5]
    
    $PGUSER = $env:PGUSER
    $PGPASSWORD = $env:PGPASSWORD
    $PGHOST = $env:PGHOST
    $PGPORT = $env:PGPORT
    $PGDATABASE = $env:PGDATABASE
    
    Write-Host "✅ Conectando: $PGHOST:$PGPORT/$PGDATABASE como $PGUSER`n" -ForegroundColor Green
} else {
    Write-Host "❌ DATABASE_URL inválido: $dbUrl" -ForegroundColor Red
    exit 1
}

# =====================================
# CHECKS
# =====================================

# 1. Alembic instalado
Test-Check -Name "Alembic instalado" `
    -Command "python -m alembic --version" `
    -ExpectedPattern "alembic"

# 2. Versão atual é 001_baseline
Test-Check -Name "Versão atual = 001_baseline" `
    -Command "python -m alembic current" `
    -ExpectedPattern "001_baseline.*head"

# 3. alembic_version em schema core
Test-Check -Name "alembic_version em core" `
    -Command "SELECT table_schema FROM information_schema.tables WHERE table_name = 'alembic_version'" `
    -ExpectedPattern "core" `
    -IsSQL

# 4. Schema core existe
Test-Check -Name "Schema core existe" `
    -Command "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'core'" `
    -ExpectedPattern "core" `
    -IsSQL

# 5. Extensão pgcrypto
Test-Check -Name "Extensão pgcrypto" `
    -Command "SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'" `
    -ExpectedPattern "pgcrypto" `
    -IsSQL

# 6. 3 tabelas criadas
Test-Check -Name "3 tabelas em core" `
    -Command "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'core' AND table_type = 'BASE TABLE'" `
    -ExpectedPattern "^3$" `
    -IsSQL

# 7. Tabela users existe
Test-Check -Name "Tabela core.users" `
    -Command "SELECT table_name FROM information_schema.tables WHERE table_schema = 'core' AND table_name = 'users'" `
    -ExpectedPattern "users" `
    -IsSQL

# 8. is_active NOT NULL
Test-Check -Name "users.is_active NOT NULL" `
    -Command "SELECT is_nullable FROM information_schema.columns WHERE table_schema = 'core' AND table_name = 'users' AND column_name = 'is_active'" `
    -ExpectedPattern "NO" `
    -IsSQL

# 9. CHECK constraint com 4 roles
Test-Check -Name "CHECK 4 roles (admin/user/technician/finance)" `
    -Command "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'check_user_role'" `
    -ExpectedPattern "(admin.*user.*technician.*finance|finance.*technician.*user.*admin)" `
    -IsSQL

# 10. Tabela financial_entries
Test-Check -Name "Tabela core.financial_entries" `
    -Command "SELECT table_name FROM information_schema.tables WHERE table_schema = 'core' AND table_name = 'financial_entries'" `
    -ExpectedPattern "financial_entries" `
    -IsSQL

# 11. Índice DESC
Test-Check -Name "Índice user_occurred com DESC" `
    -Command "SELECT indexdef FROM pg_indexes WHERE indexname = 'idx_financial_entries_user_occurred'" `
    -ExpectedPattern "occurred_at DESC" `
    -IsSQL

# 12. Partial index
Test-Check -Name "Partial index order_id" `
    -Command "SELECT indexdef FROM pg_indexes WHERE indexname = 'idx_financial_entries_order'" `
    -ExpectedPattern "WHERE.*order_id IS NOT NULL" `
    -IsSQL

# =====================================
# RESULTADO FINAL
# =====================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESULTADO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$TOTAL = $PASSED + $FAILED

Write-Host "Total:  $TOTAL checks" -ForegroundColor White
Write-Host "Passed: $PASSED ✅" -ForegroundColor Green
Write-Host "Failed: $FAILED ❌" -ForegroundColor $(if ($FAILED -eq 0) { "Green" } else { "Red" })

if ($FAILED -eq 0) {
    Write-Host "`n🟢 ETAPA 3B: READY FOR PRODUCTION`n" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n🔴 ETAPA 3B: FALHAS DETECTADAS`n" -ForegroundColor Red
    Write-Host "Execute os comandos de teste manual em:" -ForegroundColor Yellow
    Write-Host "docs/COMANDOS_TESTE_ETAPA3B_EXECUTAVEIS.md`n" -ForegroundColor Yellow
    exit 1
}

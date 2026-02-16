#!/usr/bin/env pwsh
# =====================================
# Script de Migração Alembic (PowerShell)
# ETAPA 3B - Database Migrations
# =====================================
#
# Uso:
#   .\scripts\migrate.ps1 upgrade       # Aplica todas migrations pendentes
#   .\scripts\migrate.ps1 downgrade -1  # Reverte última migration
#   .\scripts\migrate.ps1 current       # Mostra versão atual
#   .\scripts\migrate.ps1 history       # Histórico de migrations
#   .\scripts\migrate.ps1 stamp head    # Marca como aplicada (banco existente)
#
# =====================================

param(
    [Parameter(Position=0, Mandatory=$true)]
    [string]$Command,
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Cores para output
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error-Custom { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }

# =====================================
# Validar ambiente
# =====================================
$BackendDir = Join-Path $PSScriptRoot ".." "backend"
$AlembicIni = Join-Path $BackendDir "alembic.ini"
$EnvFile = Join-Path $BackendDir ".env"

if (-not (Test-Path $AlembicIni)) {
    Write-Error-Custom "alembic.ini não encontrado em: $AlembicIni"
    exit 1
}

if (-not (Test-Path $EnvFile)) {
    Write-Error-Custom "Arquivo .env não encontrado em: $EnvFile"
    Write-Info "Crie o arquivo .env com DATABASE_URL configurado"
    exit 1
}

# =====================================
# Ativar venv (se existir)
# =====================================
$VenvActivate = Join-Path $BackendDir ".venv" "Scripts" "Activate.ps1"
if (Test-Path $VenvActivate) {
    Write-Info "Ativando ambiente virtual..."
    & $VenvActivate
} else {
    Write-Info "Ambiente virtual não encontrado, usando Python global"
}

# =====================================
# Verificar Alembic instalado
# =====================================
try {
    $null = & python -m alembic --version 2>&1
} catch {
    Write-Error-Custom "Alembic não está instalado"
    Write-Info "Execute: pip install -r requirements.txt"
    exit 1
}

# =====================================
# Executar comando Alembic
# =====================================
Push-Location $BackendDir

Write-Info "Executando: alembic $Command $($Args -join ' ')"
Write-Host ""

switch ($Command.ToLower()) {
    "upgrade" {
        $Target = if ($Args.Count -gt 0) { $Args[0] } else { "head" }
        & python -m alembic upgrade $Target
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Migration aplicada com sucesso!"
        } else {
            Write-Error-Custom "Falha ao aplicar migration"
            Pop-Location
            exit 1
        }
    }
    
    "downgrade" {
        $Target = if ($Args.Count -gt 0) { $Args[0] } else { "-1" }
        Write-Host "⚠️  ATENÇÃO: Downgrade pode remover dados!" -ForegroundColor Yellow
        $Confirm = Read-Host "Confirma downgrade para '$Target'? (s/N)"
        if ($Confirm -eq 's' -or $Confirm -eq 'S') {
            & python -m alembic downgrade $Target
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Downgrade executado com sucesso"
            } else {
                Write-Error-Custom "Falha no downgrade"
                Pop-Location
                exit 1
            }
        } else {
            Write-Info "Downgrade cancelado"
        }
    }
    
    "current" {
        & python -m alembic current
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Falha ao obter versão atual"
            Pop-Location
            exit 1
        }
    }
    
    "history" {
        & python -m alembic history --verbose
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Falha ao obter histórico"
            Pop-Location
            exit 1
        }
    }
    
    "stamp" {
        $Target = if ($Args.Count -gt 0) { $Args[0] } else { "head" }
        Write-Info "Marcando database na versão: $Target"
        & python -m alembic stamp $Target
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database marcado como versão: $Target"
        } else {
            Write-Error-Custom "Falha ao marcar versão"
            Pop-Location
            exit 1
        }
    }
    
    "revision" {
        Write-Info "Criando nova migration..."
        & python -m alembic revision --autogenerate $Args
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Migration criada! Revise o arquivo antes de aplicar."
        } else {
            Write-Error-Custom "Falha ao criar migration"
            Pop-Location
            exit 1
        }
    }
    
    default {
        Write-Error-Custom "Comando desconhecido: $Command"
        Write-Host ""
        Write-Host "Comandos disponíveis:"
        Write-Host "  upgrade [target]     - Aplica migrations (padrão: head)"
        Write-Host "  downgrade [target]   - Reverte migrations (padrão: -1)"
        Write-Host "  current              - Mostra versão atual"
        Write-Host "  history              - Lista todas migrations"
        Write-Host "  stamp [target]       - Marca versão sem executar (padrão: head)"
        Write-Host "  revision [args]      - Cria nova migration"
        Pop-Location
        exit 1
    }
}

Pop-Location
Write-Host ""
Write-Success "Operação concluída"

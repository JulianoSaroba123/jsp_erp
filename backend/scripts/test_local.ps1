# ============================================================================
# test_local.ps1 - Script oficial para rodar testes do backend
# ============================================================================
# USO: cd backend; .\scripts\test_local.ps1
# REQUER: PostgreSQL rodando + DB jsp_erp_test criado
# ============================================================================

$ErrorActionPreference = "Stop"

# Navigate to backend/ directory (parent of scripts/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptDir "..")

Write-Host "Working directory: $(Get-Location)" -ForegroundColor Cyan

# Load .env.test if exists (DX: avoid hardcoded credentials)
if (Test-Path ".env.test") {
    Write-Host "Carregando .env.test..." -ForegroundColor Cyan
    Get-Content ".env.test" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$name" -Value $value
        }
    }
}

# Set DATABASE_URL_TEST (fallback if not from .env.test)
if (-not $env:DATABASE_URL_TEST) {
    $env:DATABASE_URL_TEST = "postgresql://jsp_user:Admin123@localhost:5432/jsp_erp_test"
    Write-Host "DATABASE_URL_TEST setado (fallback): $env:DATABASE_URL_TEST" -ForegroundColor Green
} else {
    Write-Host "DATABASE_URL_TEST ja configurado: $env:DATABASE_URL_TEST" -ForegroundColor Green
}

# Run tests
Write-Host "`nRodando testes (esperando 38/38)..." -ForegroundColor Yellow
pytest -q --tb=short

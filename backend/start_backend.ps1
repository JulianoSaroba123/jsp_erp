# Script para iniciar o backend FastAPI
Set-Location "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Iniciando Backend FastAPI..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Testar se app existe
if (Test-Path ".\app") {
    Write-Host "✓ Módulo app encontrado" -ForegroundColor Green
} else {
    Write-Host "✗ Módulo app NÃO encontrado!" -ForegroundColor Red
    exit 1
}

# Iniciar uvicorn
Write-Host "Iniciando uvicorn na porta 8000..." -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

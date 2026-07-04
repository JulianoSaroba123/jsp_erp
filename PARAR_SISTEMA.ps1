# ========================================
# SCRIPT DE PARADA DO JSP ERP
# ========================================

$ErrorActionPreference = "SilentlyContinue"

function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "              PARANDO SISTEMA JSP ERP                       " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

Set-Location "$PSScriptRoot"

# Parar processos Python (uvicorn/backend)
Write-Info "Parando backend..."
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force
    Write-Success "Backend parado!"
} else {
    Write-Host "Backend não estava rodando." -ForegroundColor Gray
}

# Parar processos Node (frontend)
Write-Info "Parando frontend..."
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*jsp-erp*" }
if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force
    Write-Success "Frontend parado!"
} else {
    Write-Host "Frontend não estava rodando." -ForegroundColor Gray
}

# Parar containers Docker
Write-Info "Parando banco de dados..."
docker-compose down 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Success "Banco de dados parado!"
} else {
    Write-Host "Banco de dados já estava parado." -ForegroundColor Gray
}

# Fechar janelas PowerShell do sistema
Write-Info "Fechando janelas do sistema..."
Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { 
    $_.MainWindowTitle -like "*JSP ERP*" 
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Limpar scripts temporários
Remove-Item -Path ".\backend\.start_backend_temp.ps1" -ErrorAction SilentlyContinue
Remove-Item -Path ".\frontend\.start_frontend_temp.ps1" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Sistema JSP ERP parado completamente!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Start-Sleep -Seconds 2

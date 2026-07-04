# ========================================
# SCRIPT DE INICIALIZAÇÃO DO JSP ERP
# ========================================
# Este script inicia todo o sistema automaticamente como um aplicativo:
# 1. Docker Desktop (em background)
# 2. Banco de dados PostgreSQL (em background)
# 3. Backend FastAPI (em background)
# 4. Frontend React (abre no navegador)
# ========================================

$ErrorActionPreference = "Stop"
$HOST_UI = (Get-Host).UI.RawUI
$HOST_UI.WindowTitle = "JSP ERP - Inicializando Sistema..."

# Cores para output
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "[AVISO] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERRO] $msg" -ForegroundColor Red }

# Funcao para abrir no navegador
function Open-Browser {
    param($url)
    Start-Process $url
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                    JSP ERP SYSTEM                          " -ForegroundColor Cyan
Write-Host "              Inicializacao Automatizada                    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ========================================
# ETAPA 1: Verificar e Iniciar Docker
# ========================================
Write-Info "Verificando Docker Desktop..."

$dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue

if ($null -eq $dockerProcess) {
    Write-Warning "Docker Desktop não está rodando. Iniciando..."
    
    # Tentar encontrar o executável do Docker Desktop
    $dockerPaths = @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Programs\Docker\Docker\Docker Desktop.exe"
    )
    
    $dockerExe = $null
    foreach ($path in $dockerPaths) {
        if (Test-Path $path) {
            $dockerExe = $path
            break
        }
    }
    
    if ($dockerExe) {
        Start-Process -FilePath $dockerExe
        Write-Info "Aguardando Docker Desktop iniciar (isso pode levar 1-2 minutos)..."
        
        # Aguardar até 120 segundos para Docker ficar pronto
        $timeout = 120
        $elapsed = 0
        $dockerReady = $false
        
        while ($elapsed -lt $timeout) {
            Start-Sleep -Seconds 5
            $elapsed += 5
            
            try {
                $dockerInfo = docker info 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $dockerReady = $true
                    break
                }
            } catch {
                # Docker ainda não está pronto
            }
            
            Write-Host "." -NoNewline -ForegroundColor Yellow
        }
        
        Write-Host ""
        
        if ($dockerReady) {
            Write-Success "Docker Desktop iniciado com sucesso!"
        } else {
            Write-Error "Docker Desktop não ficou pronto em tempo hábil."
            Write-Warning "Por favor, aguarde o Docker Desktop iniciar completamente e execute este script novamente."
            Start-Sleep -Seconds 5
            exit 1
        }
    } else {
        Write-Error "Docker Desktop não encontrado no sistema!"
        Write-Warning "Por favor, instale o Docker Desktop ou inicie-o manualmente."
        Start-Sleep -Seconds 5
        exit 1
    }
} else {
    # Verificar se o Docker está funcionalmente pronto
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker Desktop já está rodando!"
        } else {
            Write-Warning "Docker Desktop está iniciando... aguardando ficar pronto..."
            Start-Sleep -Seconds 10
        }
    } catch {
        Write-Warning "Docker Desktop está iniciando... aguardando ficar pronto..."
        Start-Sleep -Seconds 10
    }
}

# ========================================
# ETAPA 2: Iniciar Banco de Dados
# ========================================
Write-Host ""
Write-Info "Iniciando banco de dados PostgreSQL..."

Set-Location "$PSScriptRoot"

# Temporariamente permitir erros não-fatais para docker-compose
$previousErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"

$composeOutput = docker-compose up -d 2>&1 | Out-String

$ErrorActionPreference = $previousErrorAction

# Verificar se realmente houve erro grave
if ($composeOutput -match "error|Error|failed|Failed" -and $composeOutput -notmatch "Recreated|Running|Started|Created") {
    Write-Error "Erro ao iniciar banco de dados!"
    Write-Host "Detalhes: $composeOutput" -ForegroundColor Red
    Start-Sleep -Seconds 5
    exit 1
}

Write-Success "Banco de dados PostgreSQL iniciado!"

# Aguardar banco ficar pronto
Write-Info "Aguardando banco de dados aceitar conexões..."
Start-Sleep -Seconds 5

# Verificar se banco está acessível
$dbReady = $false
for ($i = 0; $i -lt 10; $i++) {
    $previousErrorAction2 = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    
    Set-Location "$PSScriptRoot\backend"
    $testConnection = python -c "import psycopg; conn = psycopg.connect('postgresql://jsp_user:jsp123456@localhost:5433/jsp_erp', connect_timeout=3); conn.close(); print('OK')" 2>&1
    
    $ErrorActionPreference = $previousErrorAction2
    
    if ($testConnection -match "OK") {
        $dbReady = $true
        break
    }
    
    Start-Sleep -Seconds 2
    Write-Host "." -NoNewline -ForegroundColor Yellow
}

Write-Host ""

if ($dbReady) {
    Write-Success "Banco de dados pronto para conexões!"
} else {
    Write-Warning "Banco de dados pode ainda estar inicializando..."
}

# ========================================
# ETAPA 3: Iniciar Backend FastAPI
# ========================================
Write-Host ""
Write-Info "Iniciando Backend FastAPI..."

Set-Location "$PSScriptRoot\backend"

# Verificar se ambiente virtual existe
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Info "Ambiente virtual encontrado, ativando..."
}

# Iniciar backend em background (janela minimizada)
$backendScript = @"
Set-Location '$PSScriptRoot\backend'
if (Test-Path '.venv\Scripts\Activate.ps1') {
    .\.venv\Scripts\Activate.ps1
}
`$host.ui.RawUI.WindowTitle = 'JSP ERP - Backend API (Porta 8000)'
Write-Host '============================================================' -ForegroundColor Green
Write-Host 'JSP ERP - BACKEND FASTAPI RODANDO' -ForegroundColor Green
Write-Host 'URL: http://localhost:8000' -ForegroundColor Cyan
Write-Host 'Docs: http://localhost:8000/docs' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Green
Write-Host ''
Write-Host 'Mantenha esta janela aberta enquanto usa o sistema.' -ForegroundColor Yellow
Write-Host 'Para parar o backend, feche esta janela ou pressione Ctrl+C' -ForegroundColor Gray
Write-Host ''
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

$backendScriptPath = "$PSScriptRoot\backend\.start_backend_temp.ps1"
$backendScript | Out-File -FilePath $backendScriptPath -Encoding UTF8

# Iniciar em janela minimizada
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "powershell.exe"
$processInfo.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$backendScriptPath`""
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
$backendProcess = [System.Diagnostics.Process]::Start($processInfo)

Write-Success "Backend iniciado em background!"
Write-Info "Aguardando backend ficar pronto..."
Start-Sleep -Seconds 5

# ========================================
# ETAPA 4: Verificar e Iniciar Frontend
# ========================================
Write-Host ""
Write-Info "Verificando frontend..."

Set-Location "$PSScriptRoot\frontend"

$frontendUrl = $null

if (Test-Path "package.json") {
    Write-Info "Frontend React detectado! Iniciando..."
    
    $frontendScript = @"
Set-Location '$PSScriptRoot\frontend'
`$host.ui.RawUI.WindowTitle = 'JSP ERP - Frontend React (Porta 5173)'
Write-Host '============================================================' -ForegroundColor Blue
Write-Host 'JSP ERP - FRONTEND REACT RODANDO' -ForegroundColor Blue
Write-Host 'URL: http://localhost:5173' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Blue
Write-Host ''
Write-Host 'Mantenha esta janela aberta enquanto usa o sistema.' -ForegroundColor Yellow
Write-Host 'Para parar o frontend, feche esta janela ou pressione Ctrl+C' -ForegroundColor Gray
Write-Host ''
npm run dev
"@
    
    $frontendScriptPath = "$PSScriptRoot\frontend\.start_frontend_temp.ps1"
    $frontendScript | Out-File -FilePath $frontendScriptPath -Encoding UTF8
    
    # Iniciar em janela minimizada
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = "powershell.exe"
    $processInfo.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$frontendScriptPath`""
    $processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
    $frontendProcess = [System.Diagnostics.Process]::Start($processInfo)
    
    Write-Success "Frontend iniciado em background!"
    Write-Info "Aguardando frontend compilar..."
    Start-Sleep -Seconds 8
    
    $frontendUrl = "http://localhost:5173"
} else {
    Write-Warning "Frontend não encontrado. Abrindo apenas o backend..."
    $frontendUrl = "http://localhost:8000/docs"
}

# ========================================
# FINALIZAÇÃO E ABERTURA DO SISTEMA
# ========================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "           SISTEMA JSP ERP INICIADO COM SUCESSO!            " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Servicos disponiveis:" -ForegroundColor Cyan
Write-Host "  > Banco de dados: localhost:5433" -ForegroundColor White
Write-Host "  > Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  > Documentacao: http://localhost:8000/docs" -ForegroundColor White

if (Test-Path "$PSScriptRoot\frontend\package.json") {
    Write-Host "  > Frontend: http://localhost:5173" -ForegroundColor White
}

Write-Host ""
Write-Info "Abrindo sistema no navegador..."
Start-Sleep -Seconds 2

# Abrir no navegador
if ($frontendUrl) {
    Open-Browser $frontendUrl
    Write-Success "Sistema aberto no navegador!"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "O sistema esta rodando em background!" -ForegroundColor Green
Write-Host ""
Write-Host "Para ver os logs:" -ForegroundColor Yellow
Write-Host "  > Verifique as janelas minimizadas do PowerShell" -ForegroundColor Gray
Write-Host ""
Write-Host "Para parar o sistema:" -ForegroundColor Yellow
Write-Host "  > De duplo clique em PARAR_SISTEMA.bat" -ForegroundColor Gray
Write-Host "  > Ou execute: .\PARAR_SISTEMA.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione qualquer tecla para fechar esta janela..." -ForegroundColor Gray
Write-Host "(O sistema continuara rodando em background)" -ForegroundColor Gray

$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

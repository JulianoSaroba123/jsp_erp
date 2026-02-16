# ============================================
# SCRIPT DE SETUP DO BANCO DE DADOS POSTGRESQL
# Para Windows PowerShell
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SETUP DO BANCO DE DADOS - PostgreSQL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Variáveis do ambiente
$DB_NAME = "jsp_erp"
$DB_USER = "jsp_user"
$DB_PASSWORD = "jsp123456"
$CONTAINER_NAME = "jsp_erp_db"

# Passo 1: Verificar se Docker está rodando
Write-Host "[1/6] Verificando se Docker está rodando..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>$null
if (-not $?) {
    Write-Host "ERRO: Docker não está rodando! Inicie o Docker Desktop e tente novamente." -ForegroundColor Red
    exit 1
}
Write-Host "OK - Docker está rodando" -ForegroundColor Green

# Passo 2: Verificar se o container PostgreSQL existe e está rodando
Write-Host ""
Write-Host "[2/6] Verificando container PostgreSQL..." -ForegroundColor Yellow
$containerStatus = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" 2>$null

if (-not $containerStatus) {
    Write-Host "Container nao encontrado. Tentando iniciar..." -ForegroundColor Yellow
    docker-compose up -d db
    Start-Sleep -Seconds 5
    $containerStatus = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" 2>$null
    
    if (-not $containerStatus) {
        Write-Host "ERRO: Nao foi possivel iniciar o container." -ForegroundColor Red
        exit 1
    }
}

Write-Host "OK - Container esta rodando: $containerStatus" -ForegroundColor Green

# Passo 3: Aguardar PostgreSQL estar pronto
Write-Host ""
Write-Host "[3/6] Aguardando PostgreSQL ficar pronto..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    $checkReady = docker exec $CONTAINER_NAME pg_isready -U $DB_USER -d $DB_NAME 2>$null
    if ($?) {
        $ready = $true
        Write-Host "OK - PostgreSQL está pronto!" -ForegroundColor Green
    } else {
        Write-Host "  Tentativa $attempt de $maxAttempts aguardando..." -ForegroundColor Gray
        Start-Sleep -Seconds 1
    }
}

if (-not $ready) {
    Write-Host "ERRO: PostgreSQL nao ficou pronto." -ForegroundColor Red
    exit 1
}

# Passo 4: Executar script 01_structure.sql
Write-Host ""
Write-Host "[4/6] Executando 01_structure.sql..." -ForegroundColor Yellow
Get-Content database/01_structure.sql | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - Script 01_structure.sql executado" -ForegroundColor Green
} else {
    Write-Host "ERRO ao executar 01_structure.sql" -ForegroundColor Red
    exit 1
}

# Passo 5: Executar script 03_orders.sql
Write-Host ""
Write-Host "[5/6] Executando 03_orders.sql..." -ForegroundColor Yellow
Get-Content database/03_orders.sql | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - Script 03_orders.sql executado" -ForegroundColor Green
} else {
    Write-Host "ERRO ao executar 03_orders.sql" -ForegroundColor Red
    exit 1
}

# Passo 6: Validar estrutura criada
Write-Host ""
Write-Host "[6/6] Validando estrutura do banco..." -ForegroundColor Yellow

Write-Host ""
Write-Host "  Verificando schema core..." -ForegroundColor Cyan
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\dn core"

Write-Host ""
Write-Host "  Verificando tabela core.users..." -ForegroundColor Cyan
$checkUsers = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT to_regclass('core.users');"
Write-Host "  Resultado: $checkUsers" -ForegroundColor Gray

Write-Host ""
Write-Host "  Verificando tabela core.orders..." -ForegroundColor Cyan
$checkOrders = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT to_regclass('core.orders');"
Write-Host "  Resultado: $checkOrders" -ForegroundColor Gray

if ($checkOrders -like "*core.orders*") {
    Write-Host ""
    Write-Host "OK - Tabela core.orders existe!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "AVISO: Tabela core.orders nao encontrada!" -ForegroundColor Red
}

Write-Host ""
Write-Host "  Listando colunas de core.orders..." -ForegroundColor Cyan
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\d core.orders"

Write-Host ""
Write-Host "  Contando registros em core.users..." -ForegroundColor Cyan
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_users FROM core.users;"

Write-Host ""
Write-Host "  Contando registros em core.orders..." -ForegroundColor Cyan
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_orders FROM core.orders;"

# Finalização
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SETUP CONCLUÍDO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "PROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Certifique-se que o servidor FastAPI esta rodando:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   .\run.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Teste o endpoint GET /orders:" -ForegroundColor White
Write-Host "   Invoke-WebRequest -Uri 'http://127.0.0.1:8000/orders' | Select-Object -ExpandProperty Content" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Ou abra no navegador:" -ForegroundColor White
Write-Host "   http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host ""

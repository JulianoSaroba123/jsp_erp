# ============================================================================
# BOOTSTRAP DO BANCO DE DADOS POSTGRESQL - ERP JSP
# Script para Windows PowerShell
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BOOTSTRAP BANCO DE DADOS - PostgreSQL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================
$DB_NAME = "jsp_erp"
$DB_USER = "jsp_user"
$DB_PASSWORD = "jsp123456"
$DB_HOST = "localhost"
$DB_PORT = "5432"
$CONTAINER_NAME = "jsp_erp_db"
$CONTAINER_IMAGE = "postgres"

# ============================================================================
# PASSO 1: Verificar Docker
# ============================================================================
Write-Host "[1/7] Verificando Docker..." -ForegroundColor Yellow

try {
    $null = docker --version 2>&1
    Write-Host "  OK - Docker instalado" -ForegroundColor Green
} catch {
    Write-Host "  ERRO - Docker nao encontrado. Instale Docker Desktop." -ForegroundColor Red
    exit 1
}

try {
    $null = docker ps 2>&1
    Write-Host "  OK - Docker daemon rodando" -ForegroundColor Green
} catch {
    Write-Host "  ERRO - Docker nao esta rodando. Inicie Docker Desktop." -ForegroundColor Red
    exit 1
}

# ============================================================================
# PASSO 2: Descobrir e verificar container PostgreSQL
# ============================================================================
Write-Host ""
Write-Host "[2/7] Descobrindo container PostgreSQL..." -ForegroundColor Yellow

# Tenta encontrar por nome, depois por imagem
$containerFound = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>$null

if (-not $containerFound) {
    Write-Host "  Container '$CONTAINER_NAME' nao encontrado pelo nome" -ForegroundColor Gray
    Write-Host "  Tentando encontrar por imagem postgres..." -ForegroundColor Gray
    
    $containerFound = docker ps --filter "ancestor=$CONTAINER_IMAGE" --format "{{.Names}}" | Select-Object -First 1
    
    if ($containerFound) {
        $CONTAINER_NAME = $containerFound
        Write-Host "  Container Postgres encontrado: $CONTAINER_NAME" -ForegroundColor Green
    } else {
        Write-Host "  AVISO - Nenhum container Postgres rodando" -ForegroundColor Yellow
        Write-Host "  Tentando iniciar via docker-compose..." -ForegroundColor Yellow
        
        docker-compose up -d db
        Start-Sleep -Seconds 5
        
        $containerFound = docker ps --filter "name=jsp_erp_db" --format "{{.Names}}" 2>$null
        if ($containerFound) {
            $CONTAINER_NAME = $containerFound
            Write-Host "  OK - Container iniciado: $CONTAINER_NAME" -ForegroundColor Green
        } else {
            Write-Host "  ERRO - Nao foi possivel iniciar container Postgres" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "  OK - Container encontrado: $CONTAINER_NAME" -ForegroundColor Green
}

# Verificar status
$containerStatus = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}"
Write-Host "  Status: $containerStatus" -ForegroundColor Gray

# ============================================================================
# PASSO 3: Aguardar Postgres ficar pronto
# ============================================================================
Write-Host ""
Write-Host "[3/7] Aguardando PostgreSQL aceitar conexoes..." -ForegroundColor Yellow

$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    try {
        $null = docker exec $CONTAINER_NAME pg_isready -U $DB_USER -d $DB_NAME 2>&1
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            Write-Host "  OK - PostgreSQL pronto! ($attempt tentativas)" -ForegroundColor Green
        } else {
            Write-Host "  Aguardando... $attempt/$maxAttempts" -ForegroundColor Gray
            Start-Sleep -Seconds 1
        }
    } catch {
        Write-Host "  Aguardando... $attempt/$maxAttempts" -ForegroundColor Gray
        Start-Sleep -Seconds 1
    }
}

if (-not $ready) {
    Write-Host "  ERRO - PostgreSQL nao ficou pronto em ${maxAttempts}s" -ForegroundColor Red
    Write-Host "  Verifique os logs: docker logs $CONTAINER_NAME" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# PASSO 4: Validar conectividade e contexto PRE-execução
# ============================================================================
Write-Host ""
Write-Host "[4/7] Validando conectividade (via localhost:5432)..." -ForegroundColor Yellow

# Testar conexão via localhost (mesma que FastAPI usa)
$env:PGPASSWORD = $DB_PASSWORD
try {
    $dbCheck = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT current_database();" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $currentDb = $dbCheck.Trim()
        Write-Host "  OK - Conectado em: $currentDb" -ForegroundColor Green
        
        if ($currentDb -ne $DB_NAME) {
            Write-Host "  AVISO - Banco atual ($currentDb) diferente do esperado ($DB_NAME)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ERRO - Nao foi possivel conectar via localhost:$DB_PORT" -ForegroundColor Red
        Write-Host "  Certifique-se que psql esta instalado e porta 5432 acessivel" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "  ERRO - psql nao encontrado. Instale PostgreSQL client tools." -ForegroundColor Red
    exit 1
}

# Verificar endereço do servidor (dentro vs fora do container é o mesmo Postgres)
$serverInfo = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT version();" 2>&1 | Select-Object -First 1
Write-Host "  Versao: $($serverInfo.Trim())" -ForegroundColor Gray

# Listar schemas ANTES da execução
Write-Host ""
Write-Host "  Schemas existentes ANTES:" -ForegroundColor Cyan
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dn"

# ============================================================================
# PASSO 5: Executar scripts SQL
# ============================================================================
Write-Host ""
Write-Host "[5/7] Executando scripts SQL..." -ForegroundColor Yellow

# Script 1: Estrutura (schema core, tabela users)
Write-Host ""
Write-Host "  Executando: database\01_structure.sql" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"
Get-Content "database\01_structure.sql" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --quiet -v ON_ERROR_STOP=0 > $null 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

Write-Host "  OK - 01_structure.sql executado" -ForegroundColor Green

# Script 2: Seed users (usuários iniciais)
Write-Host ""
Write-Host "  Executando: database\02_seed_users.sql" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"
Get-Content "database\02_seed_users.sql" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --quiet -v ON_ERROR_STOP=0 > $null 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

Write-Host "  OK - 02_seed_users.sql executado" -ForegroundColor Green

# Script 3: Tabela orders
Write-Host ""
Write-Host "  Executando: database\03_orders.sql" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"
Get-Content "database\03_orders.sql" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --quiet -v ON_ERROR_STOP=0 > $null 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

Write-Host "  OK - 03_orders.sql executado" -ForegroundColor Green

# Script 4: Tabela users (garantir estrutura idempotente)
Write-Host ""
Write-Host "  Executando: database\04_users.sql" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"
Get-Content "database\04_users.sql" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --quiet -v ON_ERROR_STOP=0 > $null 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

Write-Host "  OK - 04_users.sql executado" -ForegroundColor Green

# Script 5: Auth setup (índices e constraints adicionais)
Write-Host ""
Write-Host "  Executando: database\04_auth_setup.sql" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"
Get-Content "database\04_auth_setup.sql" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --quiet -v ON_ERROR_STOP=0 > $null 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

Write-Host "  OK - 04_auth_setup.sql executado" -ForegroundColor Green

# Script 6: Financial entries (ETAPA 3A)
Write-Host ""
Write-Host "  Executando: database\05_financial.sql" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"
Get-Content "database\05_financial.sql" | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --quiet -v ON_ERROR_STOP=0 > $null 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

Write-Host "  OK - 05_financial.sql executado (Lancamentos Financeiros)" -ForegroundColor Green

# ============================================================================
# PASSO 6: Validação completa POS-execução
# ============================================================================
Write-Host ""
Write-Host "[6/7] Validando estrutura criada..." -ForegroundColor Yellow

# 6.1: Verificar schemas
Write-Host ""
Write-Host "  Verificando schema 'core'..." -ForegroundColor Cyan
$schemaExists = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'core';" 2>&1
$schemaExists = $schemaExists.Trim()

if ($schemaExists -eq "1") {
    Write-Host "  OK - Schema 'core' existe" -ForegroundColor Green
} else {
    Write-Host "  ERRO - Schema 'core' NAO existe!" -ForegroundColor Red
    exit 1
}

# 6.2: Verificar tabela users
Write-Host ""
Write-Host "  Verificando tabela 'core.users'..." -ForegroundColor Cyan
$usersExists = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT to_regclass('core.users');" 2>&1
$usersExists = $usersExists.Trim()

if ($usersExists -eq "core.users") {
    Write-Host "  OK - Tabela 'core.users' existe" -ForegroundColor Green
    
    $userCount = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM core.users;" 2>&1
    Write-Host "  Total de usuarios: $($userCount.Trim())" -ForegroundColor Gray
} else {
    Write-Host "  ERRO - Tabela 'core.users' NAO existe!" -ForegroundColor Red
    exit 1
}

# 6.3: Verificar tabela orders (SMOKE CHECK CRÍTICO)
Write-Host ""
Write-Host "  Verificando tabela 'core.orders' (SMOKE CHECK)..." -ForegroundColor Cyan
$ordersExists = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT to_regclass('core.orders');" 2>&1
$ordersExists = $ordersExists.Trim()

if ($ordersExists -eq "core.orders") {
    Write-Host "  OK - Tabela 'core.orders' existe" -ForegroundColor Green
    
    $orderCount = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM core.orders;" 2>&1
    Write-Host "  Total de pedidos: $($orderCount.Trim())" -ForegroundColor Gray
    
    # Mostrar estrutura
    Write-Host ""
    Write-Host "  Estrutura da tabela core.orders:" -ForegroundColor Cyan
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\d core.orders"
} else {
    Write-Host "  ERRO CRITICO - Tabela 'core.orders' NAO existe!" -ForegroundColor Red
    Write-Host "  FastAPI vai falhar ao tentar acessar esta tabela." -ForegroundColor Red
    exit 1
}

# 6.4: Verificar via information_schema (validação alternativa)
Write-Host ""
Write-Host "  Validacao via information_schema..." -ForegroundColor Cyan
$tableCheck = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'core' AND table_name = 'orders';" 2>&1
$tableCheck = $tableCheck.Trim()

if ($tableCheck -eq "1") {
    Write-Host "  OK - Tabela confirmada via information_schema" -ForegroundColor Green
} else {
    Write-Host "  ERRO - Tabela NAO encontrada via information_schema" -ForegroundColor Red
    exit 1
}

# ============================================================================
# PASSO 7: Resumo final
# ============================================================================
Write-Host ""
Write-Host "[7/7] Resumo da configuracao..." -ForegroundColor Yellow
Write-Host ""

$summary = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT 
    current_database() as database,
    current_user as user,
    inet_server_addr() as server_addr,
    inet_server_port() as server_port;
" 2>&1

Write-Host "  Conexao validada:" -ForegroundColor Cyan
Write-Host "  $summary" -ForegroundColor Gray

# Limpar variável de senha
$env:PGPASSWORD = $null

# ============================================================================
# FINALIZAÇÃO
# ============================================================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BOOTSTRAP CONCLUIDO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "PROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Certifique-se que o FastAPI esta rodando:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   .\run.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Teste os endpoints:" -ForegroundColor White
Write-Host ""
Write-Host "   # GET - Listar pedidos" -ForegroundColor Gray
Write-Host "   Invoke-WebRequest -Uri 'http://127.0.0.1:8000/orders' | Select-Object -ExpandProperty Content" -ForegroundColor Gray
Write-Host ""
Write-Host "   # POST - Criar pedido (substitua USER_ID por UUID valido)" -ForegroundColor Gray
Write-Host "   `$body = '{\"user_id\":\"UUID_AQUI\",\"description\":\"Teste\",\"total\":100.50}'" -ForegroundColor Gray
Write-Host "   Invoke-WebRequest -Uri 'http://127.0.0.1:8000/orders' -Method POST -Body `$body -ContentType 'application/json'" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Acesse a documentacao interativa:" -ForegroundColor White
Write-Host "   http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""

# ✅ CHECKLIST DE PRONTIDÃO - ETAPA 1

**Objetivo:** Validar que todo o ambiente está funcionando corretamente antes de prosseguir.

**Tempo estimado:** 5-10 minutos

---

## 📋 RESUMO DO CHECKLIST

- [ ] **Passo 1:** Docker Desktop rodando
- [ ] **Passo 2:** Container PostgreSQL ativo
- [ ] **Passo 3:** Bootstrap executado com sucesso
- [ ] **Passo 4:** Banco de dados configurado corretamente
- [ ] **Passo 5:** FastAPI respondendo
- [ ] **Passo 6:** Endpoints GET/POST/DELETE funcionando
- [ ] **Passo 7:** Documentação interativa acessível

---

## 🚀 PASSO A PASSO (COPY-PASTE)

### Passo 1: Verificar Docker Desktop

```powershell
# Verificar se Docker está rodando
docker --version
docker ps
```

**✅ Resultado esperado:**
```
Docker version 24.x.x
CONTAINER ID   IMAGE            STATUS
...            postgres:16      Up X minutes
```

**❌ Se falhar:**
- Abra Docker Desktop e aguarde inicializar
- Execute `docker-compose up -d` no diretório do projeto

---

### Passo 2: Verificar Container PostgreSQL

```powershell
# Verificar container específico
docker ps | Select-String "postgres"

# Ver status detalhado
docker ps --filter "name=jsp_erp_db" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**✅ Resultado esperado:**
```
NAMES         STATUS              PORTS
jsp_erp_db    Up X minutes        0.0.0.0:5432->5432/tcp
```

**❌ Se container não estiver rodando:**
```powershell
# Iniciar container
docker-compose up -d db

# Aguardar 5 segundos
Start-Sleep -Seconds 5

# Verificar logs
docker logs jsp_erp_db --tail 20
```

---

### Passo 3: Executar Bootstrap

```powershell
# Certifique-se de estar no diretório raiz do projeto
cd "C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp"

# Executar bootstrap
.\bootstrap_database.ps1
```

**✅ Resultado esperado:**
```
============================================
  BOOTSTRAP BANCO DE DADOS - PostgreSQL
============================================

[1/7] Verificando Docker...
  OK - Docker daemon rodando

[2/7] Descobrindo container PostgreSQL...
  OK - Container encontrado: jsp_erp_db

[3/7] Aguardando PostgreSQL...
  OK - PostgreSQL pronto! (1 tentativas)

[4/7] Validando conectividade...
  OK - Conectado em: jsp_erp

[5/7] Executando scripts SQL...
  OK - 01_structure.sql executado
  OK - 03_orders.sql executado

[6/7] Validando estrutura:
  OK - Schema 'core' existe
  OK - Tabela 'core.users' existe (3 users)
  OK - Tabela 'core.orders' existe (3 orders)

[7/7] Resumo da configuração...
  Connection validated to jsp_erp @ ::1:5432

============================================
  BOOTSTRAP CONCLUÍDO COM SUCESSO!
============================================
```

**❌ Se SMOKE CHECK falhar:**
```powershell
# Ver se tabela existe via psql
$env:PGPASSWORD="jsp123456"
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT to_regclass('core.orders');"

# Deve retornar: core.orders
# Se retornar NULL, reexecutar bootstrap
```

---

### Passo 4: Validar Banco de Dados (Manual)

```powershell
# Definir senha como variável de ambiente
$env:PGPASSWORD="jsp123456"

# 4.1: Verificar conexão
Write-Host "`n[4.1] Testando conexão..." -ForegroundColor Yellow
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT current_database();"

# 4.2: Listar schemas
Write-Host "`n[4.2] Listando schemas..." -ForegroundColor Yellow
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "\dn"

# 4.3: Verificar tabelas em core
Write-Host "`n[4.3] Verificando tabelas..." -ForegroundColor Yellow
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "\dt core.*"

# 4.4: Validar core.orders existe
Write-Host "`n[4.4] Validando core.orders..." -ForegroundColor Yellow
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT to_regclass('core.orders');"

# 4.5: Contar registros
Write-Host "`n[4.5] Contando registros..." -ForegroundColor Yellow
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT COUNT(*) as total_users FROM core.users;"
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT COUNT(*) as total_orders FROM core.orders;"

# Limpar senha
$env:PGPASSWORD=$null
```

**✅ Resultados esperados:**
- 4.1: `jsp_erp`
- 4.2: Schema `core` listado
- 4.3: Tabelas `core.users` e `core.orders` listadas
- 4.4: `core.orders`
- 4.5: 3 users, 3+ orders

---

### Passo 5: Iniciar FastAPI

```powershell
# Abrir novo terminal PowerShell
cd "C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"

# Método 1: Via script
.\run.ps1

# OU Método 2: Manual
& .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**✅ Resultado esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using StatReload
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**❌ Se falhar com erro de importação:**
```powershell
# Verificar ambiente virtual
cd backend
& .venv\Scripts\python.exe --version

# Reinstalar dependências
& .venv\Scripts\python.exe -m pip install -r requirements.txt
```

**❌ Se falhar com erro de conexão DB:**
- Verificar DATABASE_URL em `backend/app/config.py`
- Deve ser: `postgresql+psycopg://jsp_user:jsp123456@localhost:5432/jsp_erp`

---

### Passo 6: Testar Endpoints

**Abrir NOVO terminal PowerShell** (deixar FastAPI rodando no outro):

#### 6.1: Health Check

```powershell
Write-Host "`n[6.1] Testando Health Check..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing | Select-Object StatusCode
```

**✅ Esperado:** `StatusCode : 200`

---

#### 6.2: GET /orders (Listar)

```powershell
Write-Host "`n[6.2] Testando GET /orders..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json

Write-Host "Total de pedidos: $($response.total)" -ForegroundColor Green
Write-Host "Página: $($response.page) | Tamanho: $($response.page_size)" -ForegroundColor Gray
```

**✅ Esperado:**
```
Total de pedidos: 3
Página: 1 | Tamanho: 20
```

---

#### 6.3: POST /orders (Criar)

```powershell
Write-Host "`n[6.3] Testando POST /orders..." -ForegroundColor Yellow

# Obter user_id válido
$env:PGPASSWORD="jsp123456"
$userId = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT id FROM core.users LIMIT 1;" | ForEach-Object { $_.Trim() }
$env:PGPASSWORD=$null

# Criar pedido
$body = @{
    user_id = $userId
    description = "Teste de prontidao - $(Get-Date -Format 'HH:mm:ss')"
    total = 149.90
} | ConvertTo-Json

$newOrder = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json

Write-Host "Pedido criado com ID: $($newOrder.id)" -ForegroundColor Green
Write-Host "Descrição: $($newOrder.description)" -ForegroundColor Gray
Write-Host "Total: R$ $($newOrder.total)" -ForegroundColor Gray
```

**✅ Esperado:**
```
Pedido criado com ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Descrição: Teste de prontidao - 14:32:15
Total: R$ 149.90
```

---

#### 6.4: DELETE /orders/{id} (Remover)

```powershell
Write-Host "`n[6.4] Testando DELETE /orders..." -ForegroundColor Yellow

# Listar pedidos e pegar primeiro ID
$orders = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json

$orderIdToDelete = $orders.items[0].id
Write-Host "Deletando pedido: $orderIdToDelete" -ForegroundColor Gray

# Deletar
$deleteResult = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders/$orderIdToDelete" `
    -Method DELETE `
    -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json

Write-Host "Resultado: ok = $($deleteResult.ok)" -ForegroundColor Green
```

**✅ Esperado:**
```
Deletando pedido: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Resultado: ok = True
```

---

### Passo 7: Documentação Interativa (Swagger UI)

```powershell
# Abrir Swagger UI no navegador
Start-Process "http://127.0.0.1:8000/docs"
```

**✅ Verificações manuais:**
1. Página carrega sem erros?
2. Endpoints listados:
   - `GET /health`
   - `GET /orders`
   - `POST /orders`
   - `DELETE /orders/{order_id}`
3. "Try it out" funciona?

---

## 🎯 SCRIPT COMPLETO (TUDO DE UMA VEZ)

```powershell
# ============================================================================
# SCRIPT DE PRONTIDÃO COMPLETO - ETAPA 1
# Execute este script para validar todo o ambiente
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CHECKLIST DE PRONTIDÃO - ETAPA 1" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$failed = $false

# PASSO 1: Docker
Write-Host "[1/7] Verificando Docker..." -ForegroundColor Yellow
try {
    $null = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Docker rodando" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Docker não está rodando" -ForegroundColor Red
        $failed = $true
    }
} catch {
    Write-Host "  ❌ Docker não encontrado" -ForegroundColor Red
    $failed = $true
}

# PASSO 2: Container PostgreSQL
Write-Host "`n[2/7] Verificando container PostgreSQL..." -ForegroundColor Yellow
$container = docker ps --filter "name=jsp_erp_db" --format "{{.Names}}" 2>$null
if ($container) {
    Write-Host "  ✅ Container '$container' ativo" -ForegroundColor Green
} else {
    Write-Host "  ❌ Container 'jsp_erp_db' não encontrado" -ForegroundColor Red
    $failed = $true
}

# PASSO 3: Conectividade com banco
Write-Host "`n[3/7] Testando conectividade com banco..." -ForegroundColor Yellow
$env:PGPASSWORD="jsp123456"
try {
    $dbName = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT current_database();" 2>&1 | ForEach-Object { $_.Trim() }
    if ($dbName -eq "jsp_erp") {
        Write-Host "  ✅ Conectado em: $dbName" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Banco incorreto: $dbName" -ForegroundColor Red
        $failed = $true
    }
} catch {
    Write-Host "  ❌ Falha ao conectar (psql não instalado?)" -ForegroundColor Red
    $failed = $true
}

# PASSO 4: Validar estrutura do banco
Write-Host "`n[4/7] Validando estrutura do banco..." -ForegroundColor Yellow

# 4.1: Schema core
$schemaExists = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'core';" 2>&1 | ForEach-Object { $_.Trim() }
if ($schemaExists -eq "1") {
    Write-Host "  ✅ Schema 'core' existe" -ForegroundColor Green
} else {
    Write-Host "  ❌ Schema 'core' NÃO existe" -ForegroundColor Red
    $failed = $true
}

# 4.2: Tabela core.users
$usersExists = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT to_regclass('core.users');" 2>&1 | ForEach-Object { $_.Trim() }
if ($usersExists -eq "core.users") {
    $userCount = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT COUNT(*) FROM core.users;" 2>&1 | ForEach-Object { $_.Trim() }
    Write-Host "  ✅ Tabela 'core.users' existe ($userCount registros)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Tabela 'core.users' NÃO existe" -ForegroundColor Red
    $failed = $true
}

# 4.3: Tabela core.orders (CRÍTICO)
$ordersExists = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT to_regclass('core.orders');" 2>&1 | ForEach-Object { $_.Trim() }
if ($ordersExists -eq "core.orders") {
    $orderCount = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT COUNT(*) FROM core.orders;" 2>&1 | ForEach-Object { $_.Trim() }
    Write-Host "  ✅ Tabela 'core.orders' existe ($orderCount registros)" -ForegroundColor Green
} else {
    Write-Host "  ❌ CRÍTICO: Tabela 'core.orders' NÃO existe!" -ForegroundColor Red
    Write-Host "     Execute: .\bootstrap_database.ps1" -ForegroundColor Yellow
    $failed = $true
}

$env:PGPASSWORD=$null

# PASSO 5: FastAPI rodando
Write-Host "`n[5/7] Verificando FastAPI..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 3 2>&1
    if ($health.StatusCode -eq 200) {
        Write-Host "  ✅ FastAPI respondendo" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FastAPI retornou status: $($health.StatusCode)" -ForegroundColor Red
        $failed = $true
    }
} catch {
    Write-Host "  ❌ FastAPI não está respondendo" -ForegroundColor Red
    Write-Host "     Execute: cd backend; .\run.ps1" -ForegroundColor Yellow
    $failed = $true
}

# PASSO 6: Endpoint GET /orders
Write-Host "`n[6/7] Testando GET /orders..." -ForegroundColor Yellow
try {
    $orders = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -UseBasicParsing -TimeoutSec 3 | 
        Select-Object -ExpandProperty Content | 
        ConvertFrom-Json
    
    Write-Host "  ✅ GET /orders funcionando" -ForegroundColor Green
    Write-Host "     Total: $($orders.total) | Página: $($orders.page) | Tamanho: $($orders.page_size)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ GET /orders falhou: $_" -ForegroundColor Red
    $failed = $true
}

# PASSO 7: Swagger UI
Write-Host "`n[7/7] Verificando documentação interativa..." -ForegroundColor Yellow
try {
    $docs = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -UseBasicParsing -TimeoutSec 3 2>&1
    if ($docs.StatusCode -eq 200) {
        Write-Host "  ✅ Swagger UI acessível: http://127.0.0.1:8000/docs" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Swagger UI inacessível" -ForegroundColor Red
        $failed = $true
    }
} catch {
    Write-Host "  ❌ Swagger UI não carregou" -ForegroundColor Red
    $failed = $true
}

# RESUMO FINAL
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if (-not $failed) {
    Write-Host "  ✅ TODOS OS CHECKS PASSARAM!" -ForegroundColor Green
    Write-Host "  Ambiente 100% pronto para uso" -ForegroundColor Green
} else {
    Write-Host "  ❌ ALGUNS CHECKS FALHARAM" -ForegroundColor Red
    Write-Host "  Revise os erros acima" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
```

---

## 🐛 TROUBLESHOOTING

### ❌ "Tabela core.orders não existe"

```powershell
# Executar bootstrap
.\bootstrap_database.ps1

# Reiniciar FastAPI (fechar terminal e reabrir)
cd backend
.\run.ps1
```

---

### ❌ "FastAPI não responde"

```powershell
# Verificar se processo está rodando
Get-Process | Where-Object { $_.ProcessName -like "*python*" }

# Verificar porta 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# Se nada rodando, iniciar:
cd backend
.\run.ps1
```

---

### ❌ "psql não encontrado"

**Instalar PostgreSQL Client Tools:**
1. Baixar: https://www.postgresql.org/download/windows/
2. Instalar apenas "Command Line Tools"
3. Adicionar ao PATH: `C:\Program Files\PostgreSQL\16\bin`
4. Reabrir PowerShell

---

### ❌ "Docker não está rodando"

1. Abrir Docker Desktop
2. Aguardar mensagem "Docker is running"
3. Executar: `docker-compose up -d`

---

## 📊 CRITÉRIOS DE SUCESSO

✅ **Ambiente PRONTO** quando:
- Todos os 7 passos passarem sem erros
- GET /orders retornar JSON com paginação
- POST /orders criar novo pedido
- DELETE /orders remover pedido
- Swagger UI acessível

---

**Última atualização:** 2026-02-14  
**Versão:** 1.0  
**Status:** ✅ Pronto para uso


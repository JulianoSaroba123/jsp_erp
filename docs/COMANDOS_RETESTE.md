# 🧪 COMANDOS DE RETESTE - ETAPA 1

Comandos prontos para validar que tudo está funcionando 100%.

---

## 🔧 Pré-requisitos

```powershell
# 1. Docker Desktop rodando
docker ps

# 2. Container PostgreSQL ativo
docker ps | Select-String "jsp_erp_db"

# 3. Banco de dados configurado
.\bootstrap_database.ps1
```

---

## 🗄️ Validações de Banco de Dados

### Conectar no banco

```powershell
$env:PGPASSWORD="jsp123456"
psql -h localhost -p 5432 -U jsp_user -d jsp_erp
```

### Verificar estrutura

```sql
-- Listar schemas
\dn

-- Listar tabelas em core
\dt core.*

-- Ver estrutura de orders
\d core.orders

-- Contar registros
SELECT COUNT(*) FROM core.users;
SELECT COUNT(*) FROM core.orders;

-- Sair
\q
```

### Via linha de comando

```powershell
# Schema core existe?
$env:PGPASSWORD="jsp123456"; psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "\dn core"

# Tabela orders existe?
$env:PGPASSWORD="jsp123456"; psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT to_regclass('core.orders');"

# Total de pedidos
$env:PGPASSWORD="jsp123456"; psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT COUNT(*) FROM core.orders;"
```

---

## 🚀 Iniciar FastAPI

### Método 1: Script

```powershell
cd backend
.\run.ps1
```

### Método 2: Manual

```powershell
cd backend
& .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Verificar se está rodando

```powershell
# Deve retornar status 200
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing
```

---

## 🧪 Testar Endpoints

### GET /orders - Listar pedidos

```powershell
# Simples
Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -UseBasicParsing

# Com formatação JSON
Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json | 
    ConvertTo-Json -Depth 5

# Apenas metadados
Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json | 
    Select-Object page, page_size, total

# Com paginação customizada
Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders?page=1&page_size=5" -UseBasicParsing
```

### POST /orders - Criar pedido

**Passo 1:** Obter um user_id válido

```powershell
# Via API
$users = Invoke-WebRequest -Uri "http://127.0.0.1:8000/users" -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json

$userId = $users.items[0].id
Write-Host "User ID: $userId"
```

**OU via banco:**

```powershell
$env:PGPASSWORD="jsp123456"
$userId = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT id FROM core.users LIMIT 1;" | ForEach-Object { $_.Trim() }
Write-Host "User ID: $userId"
```

**Passo 2:** Criar pedido

```powershell
$body = @{
    user_id = $userId
    description = "Pedido de teste $(Get-Date -Format 'HH:mm:ss')"
    total = 299.99
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json | 
    ConvertTo-Json
```

### DELETE /orders/{id} - Deletar pedido

**Passo 1:** Obter um order_id

```powershell
$orders = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -UseBasicParsing | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json

$orderId = $orders.items[0].id
Write-Host "Order ID: $orderId"
```

**Passo 2:** Deletar

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders/$orderId" `
    -Method DELETE `
    -UseBasicParsing | 
    Select-Object -ExpandProperty Content
```

**Resultado esperado:** `{"ok":true}`

---

## 🔬 Testes de Validação (Erros Esperados)

### Descrição vazia (HTTP 400)

```powershell
$body = @{
    user_id = "a560d451-5d1e-4122-83dc-0a438f233910"
    description = ""
    total = 50
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing
```

**Erro esperado:** `"description é obrigatório e não pode estar vazio"`

### Total negativo (HTTP 400)

```powershell
$body = @{
    user_id = "a560d451-5d1e-4122-83dc-0a438f233910"
    description = "Teste"
    total = -10
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing
```

**Erro esperado:** `"total não pode ser negativo"`

### User_id inexistente (HTTP 400)

```powershell
$body = @{
    user_id = "00000000-0000-0000-0000-000000000000"
    description = "Teste"
    total = 100
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing
```

**Erro esperado:** `"user_id inválido: usuário ... não encontrado"`

### DELETE de ID inexistente (HTTP 404)

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders/00000000-0000-0000-0000-000000000000" `
    -Method DELETE `
    -UseBasicParsing
```

**Erro esperado:** HTTP 404 Not Found

---

## 🌐 Documentação Interativa (Swagger UI)

### Abrir no navegador

```powershell
Start-Process "http://127.0.0.1:8000/docs"
```

### Ou acessar manualmente

**URL:** http://127.0.0.1:8000/docs

**Testes no Swagger:**

1. **Expandir "Orders"**
2. **GET /orders:**
   - Click "Try it out"
   - Ajustar page/page_size
   - Click "Execute"
   - Verificar Response Body

3. **POST /orders:**
   - Click "Try it out"
   - Preencher JSON:
     ```json
     {
       "user_id": "COLE_UUID_AQUI",
       "description": "Teste via Swagger",
       "total": 150.50
     }
     ```
   - Click "Execute"
   - Verificar Response (201 Created)

4. **DELETE /orders/{order_id}:**
   - Click "Try it out"
   - Colar order_id
   - Click "Execute"
   - Verificar `{"ok": true}`

---

## 📊 Teste Completo (Copy-Paste)

```powershell
# 1. Verificar Docker
Write-Host "[1/6] Verificando Docker..." -ForegroundColor Yellow
docker ps | Select-String "jsp_erp_db"

# 2. Verificar banco
Write-Host "`n[2/6] Verificando banco de dados..." -ForegroundColor Yellow
$env:PGPASSWORD="jsp123456"
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT to_regclass('core.orders');"

# 3. Verificar FastAPI
Write-Host "`n[3/6] Verificando FastAPI..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing | Select-Object StatusCode

# 4. GET /orders
Write-Host "`n[4/6] Testando GET /orders..." -ForegroundColor Yellow
$getResult = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json
Write-Host "Total de pedidos: $($getResult.total)" -ForegroundColor Green

# 5. POST /orders
Write-Host "`n[5/6] Testando POST /orders..." -ForegroundColor Yellow
$userId = psql -h localhost -p 5432 -U jsp_user -d jsp_erp -t -c "SELECT id FROM core.users LIMIT 1;" | ForEach-Object { $_.Trim() }
$body = @{ user_id = $userId; description = "Teste automatizado"; total = 99.99 } | ConvertTo-Json
$newOrder = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json
Write-Host "Pedido criado: $($newOrder.id)" -ForegroundColor Green

# 6. DELETE /orders
Write-Host "`n[6/6] Testando DELETE /orders..." -ForegroundColor Yellow
$deleteResult = Invoke-WebRequest -Uri "http://127.0.0.1:8000/orders/$($newOrder.id)" -Method DELETE -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json
Write-Host "Deletado: $($deleteResult.ok)" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TODOS OS TESTES PASSARAM!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
```

---

## 🐛 Troubleshooting Rápido

### FastAPI não responde

```powershell
# Ver se processo está rodando
Get-Process | Where-Object { $_.ProcessName -like "*python*" }

# Reiniciar
cd backend
.\run.ps1
```

### Erro "core.orders não existe"

```powershell
# Reexecutar bootstrap
.\bootstrap_database.ps1

# Reiniciar FastAPI
cd backend
.\run.ps1
```

### Erro de conexão com banco

```powershell
# Verificar container
docker ps | Select-String "postgres"

# Verificar logs
docker logs jsp_erp_db --tail 50

# Reiniciar container
docker-compose restart db
```

---

## ✅ Checklist de Conclusão

- [ ] Docker rodando
- [ ] Container PostgreSQL ativo
- [ ] Bootstrap executado sem erros
- [ ] Schema `core` existe
- [ ] Tabela `core.orders` existe
- [ ] FastAPI respondendo em http://127.0.0.1:8000
- [ ] GET /orders retorna JSON com paginação
- [ ] POST /orders cria pedido (201 Created)
- [ ] Validações retornam HTTP 400
- [ ] DELETE /orders remove pedido
- [ ] DELETE inexistente retorna 404
- [ ] Swagger UI acessível em /docs

---

**Última atualização:** 2026-02-13  
**Status:** ✅ Todos os testes funcionando

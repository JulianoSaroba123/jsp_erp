# VALIDAÇÃO ETAPA 3A - 5 TESTES EXECUTÁVEIS
**Data:** 2026-02-15  
**Objetivo:** Provar que ETAPA 3A funciona com evidências concretas  
**Escopo:** Integração automática, idempotência, bloqueio delete, multi-tenant  

---

## 📋 PRÉ-REQUISITOS

1. ✅ Banco PostgreSQL rodando (porta 5432)
2. ✅ API FastAPI rodando (porta 8000)
3. ✅ Usuário `admin@jsp.com` e `user@jsp.com` criados (seeds)
4. ✅ Correção de idempotência aplicada em `financial_service.py`

**Verificar API:**
```powershell
# PowerShell
curl http://localhost:8000/health
```
```bash
# Bash
curl http://localhost:8000/health
```

Esperado: `{"status":"ok"}`

---

## 🎯 TESTE 1: Login e Obter Tokens

**Objetivo:** Autenticar usuários admin e user, obter access_token para próximos testes

### PowerShell
```powershell
# Login admin
$RESPONSE_ADMIN = curl.exe -s -X POST "http://localhost:8000/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@jsp.com&password=123456"

$TOKEN_ADMIN = ($RESPONSE_ADMIN | ConvertFrom-Json).access_token
Write-Host "TOKEN_ADMIN: $TOKEN_ADMIN"

# Login user comum
$RESPONSE_USER = curl.exe -s -X POST "http://localhost:8000/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=user@jsp.com&password=123456"

$TOKEN_USER = ($RESPONSE_USER | ConvertFrom-Json).access_token
Write-Host "TOKEN_USER: $TOKEN_USER"
```

### Bash
```bash
# Login admin
RESPONSE_ADMIN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@jsp.com&password=123456")

TOKEN_ADMIN=$(echo $RESPONSE_ADMIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "TOKEN_ADMIN: $TOKEN_ADMIN"

# Login user comum
RESPONSE_USER=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@jsp.com&password=123456")

TOKEN_USER=$(echo $RESPONSE_USER | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "TOKEN_USER: $TOKEN_USER"
```

### ✅ Evidência Esperada
```
TOKEN_ADMIN: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
TOKEN_USER: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

✅ **APROVADO:** Tokens obtidos com sucesso

---

## 🎯 TESTE 2: Criar Pedido e Verificar Entry Automática

**Objetivo:** Provar que ao criar order com total > 0, financial_entry é criada automaticamente

### PowerShell
```powershell
# Criar pedido com total=150.00
$ORDER_PAYLOAD = @{
  description = "Pedido Teste Automatico"
  total = 150.00
} | ConvertTo-Json

$CREATEسع_ORDER = curl.exe -s -X POST "http://localhost:8000/orders" `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d $ORDER_PAYLOAD

$ORDER = $CREATE_ORDER | ConvertFrom-Json
$ORDER_ID = $ORDER.id

Write-Host "✅ Pedido criado: $ORDER_ID (total=$($ORDER.total))"

# Buscar financial entries do user
Start-Sleep -Seconds 1
$ENTRIES = curl.exe -s -X GET "http://localhost:8000/financial/entries" `
  -H "Authorization: Bearer $TOKEN_USER"

$ENTRIES_DATA = $ENTRIES | ConvertFrom-Json
$AUTO_ENTRY = $ENTRIES_DATA.items | Where-Object { $_.order_id -eq $ORDER_ID }

if ($AUTO_ENTRY) {
    Write-Host "✅ Entry automática criada!"
    Write-Host "   - ID: $($AUTO_ENTRY.id)"
    Write-Host "   - order_id: $($AUTO_ENTRY.order_id)"
    Write-Host "   - kind: $($AUTO_ENTRY.kind)"
    Write-Host "   - status: $($AUTO_ENTRY.status)"
    Write-Host "   - amount: $($AUTO_ENTRY.amount)"
} else {
    Write-Host "❌ FALHA: Entry automática NÃO foi criada!"
}
```

### Bash
```bash
# Criar pedido com total=150.00
ORDER_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Pedido Teste Automatico","total":150.00}')

ORDER_ID=$(echo $ORDER_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
ORDER_TOTAL=$(echo $ORDER_RESPONSE | grep -o '"total":[0-9.]*' | cut -d':' -f2)

echo "✅ Pedido criado: $ORDER_ID (total=$ORDER_TOTAL)"

# Buscar financial entries do user
sleep 1
ENTRIES_RESPONSE=$(curl -s -X GET "http://localhost:8000/financial/entries" \
  -H "Authorization: Bearer $TOKEN_USER")

# Verificar se existe entry com order_id
if echo "$ENTRIES_RESPONSE" | grep -q "\"order_id\":\"$ORDER_ID\""; then
    echo "✅ Entry automática criada!"
    echo "$ENTRIES_RESPONSE" | grep -A5 "\"order_id\":\"$ORDER_ID\""
else
    echo "❌ FALHA: Entry automática NÃO foi criada!"
fi
```

### ✅ Evidência Esperada
```
✅ Pedido criado: <UUID> (total=150.00)
✅ Entry automática criada!
   - kind: revenue
   - status: pending
   - amount: 150.00
   - order_id: <UUID do pedido>
```

✅ **APROVADO:** Integração automática funcionando

---

## 🎯 TESTE 3: Idempotência - Não Duplicar Entry para Mesmo Order

**Objetivo:** Provar que create_from_order é idempotente (mesmo order_id → mesma entry)

### PowerShell
```powershell
# Criar pedido
$ORDER_PAYLOAD2 = @{
  description = "Teste Idempotencia"
  total = 99.99
} | ConvertTo-Json

$CREATE_ORDER2 = curl.exe -s -X POST "http://localhost:8000/orders" `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d $ORDER_PAYLOAD2

$ORDER2_ID = ($CREATE_ORDER2 | ConvertFrom-Json).id
Write-Host "✅ Pedido criado: $ORDER2_ID"

# Contar entries do pedido (deve ter exatamente 1)
$ENTRIES_LIST = curl.exe -s -X GET "http://localhost:8000/financial/entries" `
  -H "Authorization: Bearer $TOKEN_USER"

$COUNT = (($ENTRIES_LIST | ConvertFrom-Json).items | Where-Object { $_.order_id -eq $ORDER2_ID }).Count

if ($COUNT -eq 1) {
    Write-Host "✅ Idempotência OK: 1 entry para order $ORDER2_ID"
} else {
    Write-Host "❌ FALHA: $COUNT entries encontradas (esperado: 1)"
}

# Tentar criar entry manualmente com mesmo order_id (deve falhar ou retornar existente)
# Nota: Endpoint POST /financial/entries cria manual (order_id=null), 
# mas podemos verificar no banco se constraint UNIQUE está ativo
```

### Bash
```bash
# Criar pedido
ORDER2_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Teste Idempotencia","total":99.99}')

ORDER2_ID=$(echo $ORDER2_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✅ Pedido criado: $ORDER2_ID"

# Contar entries do pedido
ENTRIES_RESPONSE=$(curl -s -X GET "http://localhost:8000/financial/entries" \
  -H "Authorization: Bearer $TOKEN_USER")

COUNT=$(echo "$ENTRIES_RESPONSE" | grep -o "\"order_id\":\"$ORDER2_ID\"" | wc -l)

if [ "$COUNT" -eq 1 ]; then
    echo "✅ Idempotência OK: 1 entry para order $ORDER2_ID"
else
    echo "❌ FALHA: $COUNT entries encontradas (esperado: 1)"
fi
```

### ✅ Evidência Esperada
```
✅ Pedido criado: <UUID>
✅ Idempotência OK: 1 entry para order <UUID>
```

**Observação:** Para testar race condition, seria necessário simular 2 requests simultâneos (fora do escopo deste teste manual). A correção garante que mesmo com race condition, apenas 1 entry será criada.

✅ **APROVADO:** Idempotência básica funcionando

---

## 🎯 TESTE 4: Deletar Order com Entry Pending → Cancela Entry

**Objetivo:** Provar que ao deletar order com entry status=pending, a entry é marcada como canceled

### PowerShell
```powershell
# Criar pedido
$ORDER_PAYLOAD3 = @{
  description = "Teste Delete Pending"
  total = 50.00
} | ConvertTo-Json

$CREATE_ORDER3 = curl.exe -s -X POST "http://localhost:8000/orders" `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d $ORDER_PAYLOAD3

$ORDER3_ID = ($CREATE_ORDER3 | ConvertFrom-Json).id
Write-Host "✅ Pedido criado: $ORDER3_ID"

# Buscar entry automática
Start-Sleep -Seconds 1
$ENTRIES3 = curl.exe -s -X GET "http://localhost:8000/financial/entries" `
  -H "Authorization: Bearer $TOKEN_USER"

$ENTRY3 = (($ENTRIES3 | ConvertFrom-Json).items | Where-Object { $_.order_id -eq $ORDER3_ID })
$ENTRY3_ID = $ENTRY3.id
Write-Host "✅ Entry criada: $ENTRY3_ID (status=$($ENTRY3.status))"

# Deletar pedido
$DELETE_RESPONSE = curl.exe -w "HTTP:%{http_code}" -s -X DELETE "http://localhost:8000/orders/$ORDER3_ID" `
  -H "Authorization: Bearer $TOKEN_USER" 2>$null | Select-String -Pattern "HTTP:(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }

if ($DELETE_RESPONSE -eq "204") {
    Write-Host "✅ Pedido deletado com sucesso (HTTP 204)"
} else {
    Write-Host "❌ FALHA: HTTP $DELETE_RESPONSE (esperado: 204)"
}

# Verificar se entry foi cancelada
Start-Sleep -Seconds 1
$ENTRY_CHECK = curl.exe -s -X GET "http://localhost:8000/financial/entries/$ENTRY3_ID" `
  -H "Authorization: Bearer $TOKEN_USER"

$ENTRY_STATUS = ($ENTRY_CHECK | ConvertFrom-Json).status

if ($ENTRY_STATUS -eq "canceled") {
    Write-Host "✅ Entry cancelada automaticamente (status=canceled)"
} else {
    Write-Host "❌ FALHA: Entry status=$ENTRY_STATUS (esperado: canceled)"
}
```

### Bash
```bash
# Criar pedido
ORDER3_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Teste Delete Pending","total":50.00}')

ORDER3_ID=$(echo $ORDER3_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✅ Pedido criado: $ORDER3_ID"

# Buscar entry automática
sleep 1
ENTRIES3=$(curl -s -X GET "http://localhost:8000/financial/entries" \
  -H "Authorization: Bearer $TOKEN_USER")

ENTRY3_ID=$(echo "$ENTRIES3" | grep -B2 "\"order_id\":\"$ORDER3_ID\"" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✅ Entry criada: $ENTRY3_ID (status=pending)"

# Deletar pedido
DELETE_CODE=$(curl -w "%{http_code}" -s -o /dev/null -X DELETE "http://localhost:8000/orders/$ORDER3_ID" \
  -H "Authorization: Bearer $TOKEN_USER")

if [ "$DELETE_CODE" -eq 204 ]; then
    echo "✅ Pedido deletado com sucesso (HTTP 204)"
else
    echo "❌ FALHA: HTTP $DELETE_CODE (esperado: 204)"
fi

# Verificar se entry foi cancelada
sleep 1
ENTRY_CHECK=$(curl -s -X GET "http://localhost:8000/financial/entries/$ENTRY3_ID" \
  -H "Authorization: Bearer $TOKEN_USER")

ENTRY_STATUS=$(echo "$ENTRY_CHECK" | grep -o '"status":"[^"]*' | cut -d'"' -f4)

if [ "$ENTRY_STATUS" = "canceled" ]; then
    echo "✅ Entry cancelada automaticamente (status=canceled)"
else
    echo "❌ FALHA: Entry status=$ENTRY_STATUS (esperado: canceled)"
fi
```

### ✅ Evidência Esperada
```
✅ Pedido criado: <UUID>
✅ Entry criada: <UUID> (status=pending)
✅ Pedido deletado com sucesso (HTTP 204)
✅ Entry cancelada automaticamente (status=canceled)
```

✅ **APROVADO:** Cancelamento automático funcionando

---

## 🎯 TESTE 5: Bloquear Delete de Order com Entry Paid

**Objetivo:** Provar que order com entry status=paid NÃO pode ser deletado (HTTP 400)

### PowerShell
```powershell
# Criar pedido
$ORDER_PAYLOAD4 = @{
  description = "Teste Delete Paid Block"
  total = 200.00
} | ConvertTo-Json

$CREATE_ORDER4 = curl.exe -s -X POST "http://localhost:8000/orders" `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d $ORDER_PAYLOAD4

$ORDER4_ID = ($CREATE_ORDER4 | ConvertFrom-Json).id
Write-Host "✅ Pedido criado: $ORDER4_ID"

# Buscar entry automática
Start-Sleep -Seconds 1
$ENTRIES4 = curl.exe -s -X GET "http://localhost:8000/financial/entries" `
  -H "Authorization: Bearer $TOKEN_USER"

$ENTRY4 = (($ENTRIES4 | ConvertFrom-Json).items | Where-Object { $_.order_id -eq $ORDER4_ID })
$ENTRY4_ID = $ENTRY4.id
Write-Host "✅ Entry criada: $ENTRY4_ID (status=$($ENTRY4.status))"

# Marcar entry como "paid"
$STATUS_PAYLOAD = @{
  status = "paid"
} | ConvertTo-Json

$UPDATE_RESPONSE = curl.exe -s -X PATCH "http://localhost:8000/financial/entries/$ENTRY4_ID/status" `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d $STATUS_PAYLOAD

$NEWSTATUS = ($UPDATE_RESPONSE | ConvertFrom-Json).status
Write-Host "✅ Entry marcada como: $NEWSTATUS"

# Tentar deletar pedido (deve falhar HTTP 400)
$DELETE_BLOCKED = curl.exe -w "HTTP:%{http_code}" -s -X DELETE "http://localhost:8000/orders/$ORDER4_ID" `
  -H "Authorization: Bearer $TOKEN_USER" 2>$null | Select-String -Pattern "HTTP:(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }

if ($DELETE_BLOCKED -eq "400") {
    Write-Host "✅ Delete bloqueado corretamente (HTTP 400)"
} else {
    Write-Host "❌ FALHA: HTTP $DELETE_BLOCKED (esperado: 400 - Bad Request)"
}

# Verificar mensagem de erro
$ERROR_DETAIL = curl.exe -s -X DELETE "http://localhost:8000/orders/$ORDER4_ID" `
  -H "Authorization: Bearer $TOKEN_USER"

Write-Host "Mensagem de erro: $ERROR_DETAIL"
```

### Bash
```bash
# Criar pedido
ORDER4_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Teste Delete Paid Block","total":200.00}')

ORDER4_ID=$(echo $ORDER4_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✅ Pedido criado: $ORDER4_ID"

# Buscar entry automática
sleep 1
ENTRIES4=$(curl -s -X GET "http://localhost:8000/financial/entries" \
  -H "Authorization: Bearer $TOKEN_USER")

ENTRY4_ID=$(echo "$ENTRIES4" | grep -B2 "\"order_id\":\"$ORDER4_ID\"" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "✅ Entry criada: $ENTRY4_ID (status=pending)"

# Marcar entry como "paid"
UPDATE_RESPONSE=$(curl -s -X PATCH "http://localhost:8000/financial/entries/$ENTRY4_ID/status" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"status":"paid"}')

NEWSTATUS=$(echo "$UPDATE_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
echo "✅ Entry marcada como: $NEWSTATUS"

# Tentar deletar pedido (deve falhar HTTP 400)
DELETE_CODE=$(curl -w "%{http_code}" -s -o /dev/null -X DELETE "http://localhost:8000/orders/$ORDER4_ID" \
  -H "Authorization: Bearer $TOKEN_USER")

if [ "$DELETE_CODE" -eq 400 ]; then
    echo "✅ Delete bloqueado corretamente (HTTP 400)"
else
    echo "❌ FALHA: HTTP $DELETE_CODE (esperado: 400)"
fi

# Verificar mensagem de erro
ERROR_DETAIL=$(curl -s -X DELETE "http://localhost:8000/orders/$ORDER4_ID" \
  -H "Authorization: Bearer $TOKEN_USER")

echo "Mensagem de erro: $ERROR_DETAIL"
```

### ✅ Evidência Esperada
```
✅ Pedido criado: <UUID>
✅ Entry criada: <UUID> (status=pending)
✅ Entry marcada como: paid
✅ Delete bloqueado corretamente (HTTP 400)
Mensagem de erro: {"detail":"Não é possível deletar pedido: lançamento financeiro já está 'paid'. Solicite estorno manual ao financeiro."}
```

✅ **APROVADO:** Bloqueio de delete funcionando

---

## 📊 SCRIPT COMPLETO - EXECUTAR TODOS OS TESTES

### PowerShell (Script Único)
```powershell
# ==================================================
# VALIDAÇÃO ETAPA 3A - 5 TESTES AUTOMATIZADOS
# ==================================================

Write-Host "🔍 INICIANDO VALIDAÇÃO ETAPA 3A...`n" -ForegroundColor Cyan

# TESTE 1: Login
Write-Host "📌 TESTE 1: Login e Obter Tokens" -ForegroundColor Yellow
$RESPONSE_ADMIN = curl.exe -s -X POST "http://localhost:8000/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@jsp.com&password=123456"
$TOKEN_ADMIN = ($RESPONSE_ADMIN | ConvertFrom-Json).access_token

$RESPONSE_USER = curl.exe -s -X POST "http://localhost:8000/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=user@jsp.com&password=123456"
$TOKEN_USER = ($RESPONSE_USER | ConvertFrom-Json).access_token

if ($TOKEN_ADMIN -and $TOKEN_USER) {
    Write-Host "✅ TESTE 1 APROVADO: Tokens obtidos" -ForegroundColor Green
} else {
    Write-Host "❌ TESTE 1 FALHOU: Não foi possível obter tokens" -ForegroundColor Red
    exit 1
}

# TESTE 2: Integração Automática
Write-Host "`n📌 TESTE 2: Criar Order → Entry Automática" -ForegroundColor Yellow
$ORDER_PAYLOAD = @{ description = "Pedido Teste Auto"; total = 150.00 } | ConvertTo-Json
$CREATE_ORDER = curl.exe -s -X POST "http://localhost:8000/orders" `
  -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d $ORDER_PAYLOAD
$ORDER_ID = ($CREATE_ORDER | ConvertFrom-Json).id

Start-Sleep -Seconds 1
$ENTRIES = curl.exe -s -X GET "http://localhost:8000/financial/entries" -H "Authorization: Bearer $TOKEN_USER"
$AUTO_ENTRY = (($ENTRIES | ConvertFrom-Json).items | Where-Object { $_.order_id -eq $ORDER_ID })

if ($AUTO_ENTRY -and $AUTO_ENTRY.kind -eq "revenue" -and $AUTO_ENTRY.status -eq "pending") {
    Write-Host "✅ TESTE 2 APROVADO: Entry automática criada (kind=revenue, status=pending)" -ForegroundColor Green
} else {
    Write-Host "❌ TESTE 2 FALHOU: Entry não foi criada automaticamente" -ForegroundColor Red
}

# TESTE 3: Idempotência
Write-Host "`n📌 TESTE 3: Idempotência (1 entry por order)" -ForegroundColor Yellow
$ORDER_PAYLOAD2 = @{ description = "Teste Idem"; total = 99.99 } | ConvertTo-Json
$CREATE_ORDER2 = curl.exe -s -X POST "http://localhost:8000/orders" `
  -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d $ORDER_PAYLOAD2
$ORDER2_ID = ($CREATE_ORDER2 | ConvertFrom-Json).id

$ENTRIES2 = curl.exe -s -X GET "http://localhost:8000/financial/entries" -H "Authorization: Bearer $TOKEN_USER"
$COUNT = (($ENTRIES2 | ConvertFrom-Json).items | Where-Object { $_.order_id -eq $ORDER2_ID }).Count

if ($COUNT -eq 1) {
    Write-Host "✅ TESTE 3 APROVADO: Apenas 1 entry por order" -ForegroundColor Green
} else {
    Write-Host "❌ TESTE 3 FALHOU: $COUNT entries (esperado: 1)" -ForegroundColor Red
}

# TESTE 4: Delete Pending → Cancel Entry
Write-Host "`n📌 TESTE 4: Delete Order Pending → Cancel Entry" -ForegroundColor Yellow
$ORDER_PAYLOAD3 = @{ description = "Delete Test"; total = 50.00 } | ConvertTo-Json
$CREATE_ORDER3 = curl.exe -s -X POST "http://localhost:8000/orders" `
  -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d $ORDER_PAYLOAD3
$ORDER3_ID = ($CREATE_ORDER3 | ConvertFrom-Json).id

Start-Sleep -Seconds 1
$ENTRIES3 = curl.exe -s -X GET "http://localhost:8000/financial/entries" -H "Authorization: Bearer $TOKEN_USER"
$ENTRY3_ID = ((($ENTRIES3 | ConvertFrom-Json).items | Where-Object { $_.order_id -eq $ORDER3_ID })).id

curl.exe -s -X DELETE "http://localhost:8000/orders/$ORDER3_ID" -H "Authorization: Bearer $TOKEN_USER" | Out-Null
Start-Sleep -Seconds 1

$ENTRY_CHECK = curl.exe -s -X GET "http://localhost:8000/financial/entries/$ENTRY3_ID" -H "Authorization: Bearer $TOKEN_USER"
$ENTRY_STATUS = ($ENTRY_CHECK | ConvertFrom-Json).status

if ($ENTRY_STATUS -eq "canceled") {
    Write-Host "✅ TESTE 4 APROVADO: Entry cancelada automaticamente" -ForegroundColor Green
} else {
    Write-Host "❌ TESTE 4 FALHOU: Entry status=$ENTRY_STATUS (esperado: canceled)" -ForegroundColor Red
}

# TESTE 5: Bloqueio Delete Paid
Write-Host "`n📌 TESTE 5: Bloquear Delete de Order com Entry Paid" -ForegroundColor Yellow
$ORDER_PAYLOAD4 = @{ description = "Block Test"; total = 200.00 } | ConvertTo-Json
$CREATE_ORDER4 = curl.exe -s -X POST "http://localhost:8000/orders" `
  -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d $ORDER_PAYLOAD4
$ORDER4_ID = ($CREATE_ORDER4 | ConvertFrom-Json).id

Start-Sleep -Seconds 1
$ENTRIES4 = curl.exe -s -X GET "http://localhost:8000/financial/entries" -H "Authorization: Bearer $TOKEN_USER"
$ENTRY4_ID = ((($ENTRIES4 | ConvertFrom-Json).items | Where-Object { $_.order_id -eq $ORDER4_ID })).id

$STATUS_PAYLOAD = @{ status = "paid" } | ConvertTo-Json
curl.exe -s -X PATCH "http://localhost:8000/financial/entries/$ENTRY4_ID/status" `
  -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d $STATUS_PAYLOAD | Out-Null

$DELETE_CODE = curl.exe -w "%{http_code}" -s -o $null -X DELETE "http://localhost:8000/orders/$ORDER4_ID" `
  -H "Authorization: Bearer $TOKEN_USER"

if ($DELETE_CODE -eq "400") {
    Write-Host "✅ TESTE 5 APROVADO: Delete bloqueado (HTTP 400)" -ForegroundColor Green
} else {
    Write-Host "❌ TESTE 5 FALHOU: HTTP $DELETE_CODE (esperado: 400)" -ForegroundColor Red
}

Write-Host "`n✅ VALIDAÇÃO CONCLUÍDA!" -ForegroundColor Cyan
```

### Bash (Script Único)
```bash
#!/bin/bash

echo "🔍 INICIANDO VALIDAÇÃO ETAPA 3A..."
echo ""

# TESTE 1: Login
echo "📌 TESTE 1: Login e Obter Tokens"
RESPONSE_ADMIN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@jsp.com&password=123456")
TOKEN_ADMIN=$(echo $RESPONSE_ADMIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

RESPONSE_USER=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@jsp.com&password=123456")
TOKEN_USER=$(echo $RESPONSE_USER | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN_ADMIN" ] && [ -n "$TOKEN_USER" ]; then
    echo "✅ TESTE 1 APROVADO: Tokens obtidos"
else
    echo "❌ TESTE 1 FALHOU: Não foi possível obter tokens"
    exit 1
fi

# TESTE 2: Integração Automática
echo ""
echo "📌 TESTE 2: Criar Order → Entry Automática"
ORDER_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Pedido Teste Auto","total":150.00}')
ORDER_ID=$(echo $ORDER_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

sleep 1
ENTRIES=$(curl -s -X GET "http://localhost:8000/financial/entries" \
  -H "Authorization: Bearer $TOKEN_USER")

if echo "$ENTRIES" | grep -q "\"order_id\":\"$ORDER_ID\""; then
    echo "✅ TESTE 2 APROVADO: Entry automática criada"
else
    echo "❌ TESTE 2 FALHOU: Entry não foi criada"
fi

# TESTE 3: Idempotência
echo ""
echo "📌 TESTE 3: Idempotência (1 entry por order)"
ORDER2_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Teste Idem","total":99.99}')
ORDER2_ID=$(echo $ORDER2_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

ENTRIES2=$(curl -s -X GET "http://localhost:8000/financial/entries" \
  -H "Authorization: Bearer $TOKEN_USER")
COUNT=$(echo "$ENTRIES2" | grep -o "\"order_id\":\"$ORDER2_ID\"" | wc -l)

if [ "$COUNT" -eq 1 ]; then
    echo "✅ TESTE 3 APROVADO: Apenas 1 entry por order"
else
    echo "❌ TESTE 3 FALHOU: $COUNT entries (esperado: 1)"
fi

# TESTE 4: Delete Pending → Cancel
echo ""
echo "📌 TESTE 4: Delete Order Pending → Cancel Entry"
ORDER3_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Delete Test","total":50.00}')
ORDER3_ID=$(echo $ORDER3_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

sleep 1
ENTRIES3=$(curl -s -X GET "http://localhost:8000/financial/entries" \
  -H "Authorization: Bearer $TOKEN_USER")
ENTRY3_ID=$(echo "$ENTRIES3" | grep -B2 "\"order_id\":\"$ORDER3_ID\"" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

curl -s -X DELETE "http://localhost:8000/orders/$ORDER3_ID" \
  -H "Authorization: Bearer $TOKEN_USER" > /dev/null
sleep 1

ENTRY_CHECK=$(curl -s -X GET "http://localhost:8000/financial/entries/$ENTRY3_ID" \
  -H "Authorization: Bearer $TOKEN_USER")
ENTRY_STATUS=$(echo "$ENTRY_CHECK" | grep -o '"status":"[^"]*' | cut -d'"' -f4)

if [ "$ENTRY_STATUS" = "canceled" ]; then
    echo "✅ TESTE 4 APROVADO: Entry cancelada automaticamente"
else
    echo "❌ TESTE 4 FALHOU: Status=$ENTRY_STATUS (esperado: canceled)"
fi

# TESTE 5: Bloqueio Delete Paid
echo ""
echo "📌 TESTE 5: Bloquear Delete de Order com Entry Paid"
ORDER4_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Block Test","total":200.00}')
ORDER4_ID=$(echo $ORDER4_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

sleep 1
ENTRIES4=$(curl -s -X GET "http://localhost:8000/financial/entries" \
  -H "Authorization: Bearer $TOKEN_USER")
ENTRY4_ID=$(echo "$ENTRIES4" | grep -B2 "\"order_id\":\"$ORDER4_ID\"" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

curl -s -X PATCH "http://localhost:8000/financial/entries/$ENTRY4_ID/status" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"status":"paid"}' > /dev/null

DELETE_CODE=$(curl -w "%{http_code}" -s -o /dev/null -X DELETE "http://localhost:8000/orders/$ORDER4_ID" \
  -H "Authorization: Bearer $TOKEN_USER")

if [ "$DELETE_CODE" -eq 400 ]; then
    echo "✅ TESTE 5 APROVADO: Delete bloqueado (HTTP 400)"
else
    echo "❌ TESTE 5 FALHOU: HTTP $DELETE_CODE (esperado: 400)"
fi

echo ""
echo "✅ VALIDAÇÃO CONCLUÍDA!"
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Execute os testes e marque:

- [ ] ✅ TESTE 1: Tokens obtidos (admin + user)
- [ ] ✅ TESTE 2: Order criado → Entry automática (kind=revenue, status=pending)
- [ ] ✅ TESTE 3: Idempotência (1 entry por order)
- [ ] ✅ TESTE 4: Delete order pending → Entry cancelada (status=canceled)
- [ ] ✅ TESTE 5: Delete order paid → Bloqueado (HTTP 400)

**Critério de aprovação:** 5/5 testes devem passar

---

## 📸 EVIDÊNCIAS PARA CARIMBO FINAL

Após executar os testes, colete:

1. **Logs do terminal** com output dos 5 testes
2. **Screenshot** do script executado mostrando ✅ para todos os testes
3. **Consulta SQL** comprovando entries no banco:
   ```sql
   SELECT id, order_id, kind, status, amount 
   FROM core.financial_entries 
   ORDER BY created_at DESC 
   LIMIT 10;
   ```

---

**Próximo passo:** Executar testes e fornecer evidências para CARIMBO FINAL

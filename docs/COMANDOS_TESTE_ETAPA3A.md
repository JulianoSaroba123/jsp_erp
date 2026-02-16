# COMANDOS DE TESTE - ETAPA 3A (FINANCEIRO AUTOMÁTICO)

Comandos executáveis para validar a implementação do módulo financeiro.

---

## PRÉ-REQUISITOS

1. **Banco de dados bootstrapped:**
   ```powershell
   # PowerShell
   .\bootstrap_database.ps1
   
   # Bash
   ./bootstrap_database.sh
   ```

2. **API rodando:**
   ```powershell
   # PowerShell
   cd backend
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --reload
   
   # Bash
   cd backend
   source .venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

3. **Usuários seed criados:**
   - admin@jsp.com (senha: 123456)
   - user@jsp.com (senha: 123456)

---

## TESTE 1: LOGIN E OBTENÇÃO DE TOKENS

### PowerShell

```powershell
# Login admin
$adminResp = curl.exe -s -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@jsp.com&password=123456" | ConvertFrom-Json

$TOKEN_ADMIN = $adminResp.access_token
Write-Host "TOKEN ADMIN: $($TOKEN_ADMIN.Substring(0,20))..."

# Login user
$userResp = curl.exe -s -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=user@jsp.com&password=123456" | ConvertFrom-Json

$TOKEN_USER = $userResp.access_token
Write-Host "TOKEN USER: $($TOKEN_USER.Substring(0,20))..."
```

### Bash

```bash
# Login admin
TOKEN_ADMIN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@jsp.com&password=123456" | jq -r '.access_token')

echo "TOKEN ADMIN: ${TOKEN_ADMIN:0:20}..."

# Login user
TOKEN_USER=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@jsp.com&password=123456" | jq -r '.access_token')

echo "TOKEN USER: ${TOKEN_USER:0:20}..."
```

**Resultado esperado:**
- `200 OK`
- Tokens JWT válidos

---

## TESTE 2: CRIAR PEDIDO → VERIFICAR LANÇAMENTO AUTOMÁTICO

### PowerShell

```powershell
# Criar pedido
$orderPayload = @{
    description = "Venda produto XYZ - Teste ETAPA 3A"
    total = 350.00
} | ConvertTo-Json

$orderResp = curl.exe -s -X POST http://localhost:8000/orders `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d $orderPayload | ConvertFrom-Json

$ORDER_ID = $orderResp.id
Write-Host "Pedido criado: $ORDER_ID"
Write-Host "Total: $($orderResp.total)"

# Verificar lançamentos financeiros do user
$financialList = curl.exe -s -X GET "http://localhost:8000/financial/entries?kind=revenue&status=pending" `
  -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json

Write-Host "`nLancamentos financeiros do user:"
$financialList.items | ForEach-Object {
    Write-Host "  - ID: $($_.id)"
    Write-Host "    Order ID: $($_.order_id)"
    Write-Host "    Amount: $($_.amount)"
    Write-Host "    Status: $($_.status)"
    Write-Host "    Kind: $($_.kind)"
}
```

### Bash

```bash
# Criar pedido
ORDER_RESP=$(curl -s -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Venda produto XYZ - Teste ETAPA 3A",
    "total": 350.00
  }')

ORDER_ID=$(echo $ORDER_RESP | jq -r '.id')
echo "Pedido criado: $ORDER_ID"
echo "Total: $(echo $ORDER_RESP | jq -r '.total')"

# Verificar lançamentos financeiros do user
echo -e "\nLancamentos financeiros do user:"
curl -s -X GET "http://localhost:8000/financial/entries?kind=revenue&status=pending" \
  -H "Authorization: Bearer $TOKEN_USER" | jq -r '.items[] | 
  "  - ID: \(.id)\n    Order ID: \(.order_id)\n    Amount: \(.amount)\n    Status: \(.status)\n    Kind: \(.kind)"'
```

**Resultado esperado:**
- ✅ Pedido criado com `total: 350.00`
- ✅ Lançamento financeiro automático criado:
  - `kind`: revenue
  - `status`: pending
  - `amount`: 350.00
  - `order_id`: igual ao ID do pedido

---

## TESTE 3: MULTI-TENANT - USER SÓ VÊ SEUS LANÇAMENTOS

### PowerShell

```powershell
# User lista seus lançamentos
$userEntries = curl.exe -s -X GET http://localhost:8000/financial/entries `
  -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json

Write-Host "User ve $($userEntries.total) lancamento(s)"

# Admin lista todos os lançamentos
$adminEntries = curl.exe -s -X GET http://localhost:8000/financial/entries `
  -H "Authorization: Bearer $TOKEN_ADMIN" | ConvertFrom-Json

Write-Host "Admin ve $($adminEntries.total) lancamento(s)"
Write-Host "`nAdmin ve >= User? $($adminEntries.total -ge $userEntries.total)"
```

### Bash

```bash
# User lista seus lançamentos
USER_COUNT=$(curl -s -X GET http://localhost:8000/financial/entries \
  -H "Authorization: Bearer $TOKEN_USER" | jq -r '.total')

echo "User ve $USER_COUNT lancamento(s)"

# Admin lista todos os lançamentos
ADMIN_COUNT=$(curl -s -X GET http://localhost:8000/financial/entries \
  -H "Authorization: Bearer $TOKEN_ADMIN" | jq -r '.total')

echo "Admin ve $ADMIN_COUNT lancamento(s)"
echo "Admin ve >= User? $([ $ADMIN_COUNT -ge $USER_COUNT ] && echo 'true' || echo 'false')"
```

**Resultado esperado:**
- ✅ User vê apenas seus lançamentos
- ✅ Admin vê todos (total >= total do user)

---

## TESTE 4: CRIAR LANÇAMENTO MANUAL

### PowerShell

```powershell
$manualPayload = @{
    kind = "expense"
    amount = 120.50
    description = "Pagamento fornecedor ABC - Manual"
    occurred_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json

$manualEntry = curl.exe -s -X POST http://localhost:8000/financial/entries `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d $manualPayload | ConvertFrom-Json

Write-Host "Lancamento manual criado:"
Write-Host "  ID: $($manualEntry.id)"
Write-Host "  Kind: $($manualEntry.kind)"
Write-Host "  Amount: $($manualEntry.amount)"
Write-Host "  Order ID: $($manualEntry.order_id)"  # Deve ser null
```

### Bash

```bash
MANUAL_ENTRY=$(curl -s -X POST http://localhost:8000/financial/entries \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "expense",
    "amount": 120.50,
    "description": "Pagamento fornecedor ABC - Manual",
    "occurred_at": "'$(date -u +%Y-%m-%dT%H:%M:%S)'"
  }')

echo "Lancamento manual criado:"
echo "  ID: $(echo $MANUAL_ENTRY | jq -r '.id')"
echo "  Kind: $(echo $MANUAL_ENTRY | jq -r '.kind')"
echo "  Amount: $(echo $MANUAL_ENTRY | jq -r '.amount')"
echo "  Order ID: $(echo $MANUAL_ENTRY | jq -r '.order_id')"  # Deve ser null
```

**Resultado esperado:**
- ✅ Lançamento criado
- ✅ `kind`: expense
- ✅ `order_id`: null (lançamento manual)
- ✅ `status`: pending

---

## TESTE 5: ATUALIZAR STATUS (pending → paid)

### PowerShell

```powershell
# Buscar primeiro lançamento pending do user
$pendingEntry = (curl.exe -s -X GET "http://localhost:8000/financial/entries?status=pending" `
  -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json).items[0]

$ENTRY_ID = $pendingEntry.id
Write-Host "Atualizando lancamento: $ENTRY_ID"
Write-Host "  Status atual: $($pendingEntry.status)"

# Atualizar para paid
$updatePayload = @{
    status = "paid"
} | ConvertTo-Json

$updatedEntry = curl.exe -s -X PATCH "http://localhost:8000/financial/entries/$ENTRY_ID/status" `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d $updatePayload | ConvertFrom-Json

Write-Host "  Status novo: $($updatedEntry.status)"
Write-Host "  Updated at: $($updatedEntry.updated_at)"
```

### Bash

```bash
# Buscar primeiro lançamento pending do user
PENDING_ENTRY=$(curl -s -X GET "http://localhost:8000/financial/entries?status=pending" \
  -H "Authorization: Bearer $TOKEN_USER")

ENTRY_ID=$(echo $PENDING_ENTRY | jq -r '.items[0].id')
CURRENT_STATUS=$(echo $PENDING_ENTRY | jq -r '.items[0].status')

echo "Atualizando lancamento: $ENTRY_ID"
echo "  Status atual: $CURRENT_STATUS"

# Atualizar para paid
UPDATED_ENTRY=$(curl -s -X PATCH "http://localhost:8000/financial/entries/$ENTRY_ID/status" \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"status": "paid"}')

echo "  Status novo: $(echo $UPDATED_ENTRY | jq -r '.status')"
echo "  Updated at: $(echo $UPDATED_ENTRY | jq -r '.updated_at')"
```

**Resultado esperado:**
- ✅ Status atualizado: pending → paid
- ✅ `updated_at` preenchido

---

## TESTE 6: TENTAR DELETAR PEDIDO COM LANÇAMENTO PAGO (BLOQUEADO)

### PowerShell

```powershell
# Tentar deletar pedido que tem lançamento 'paid'
$deleteResp = curl.exe -s -w "`nHTTP:%{http_code}" -X DELETE "http://localhost:8000/orders/$ORDER_ID" `
  -H "Authorization: Bearer $TOKEN_USER"

$httpStatus = ($deleteResp | Select-String -Pattern "HTTP:(\d+)").Matches.Groups[1].Value

Write-Host "Tentativa de deletar pedido com lancamento 'paid':"
Write-Host "  Status HTTP: $httpStatus"

if ($httpStatus -eq "400") {
    Write-Host "  OK - Delecao bloqueada (esperado 400)" -ForegroundColor Green
} else {
    Write-Host "  ERRO - Deveria ter bloqueado com 400" -ForegroundColor Red
}
```

### Bash

```bash
# Tentar deletar pedido que tem lançamento 'paid'
DELETE_RESP=$(curl -s -w "\nHTTP:%{http_code}" -X DELETE "http://localhost:8000/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN_USER")

HTTP_STATUS=$(echo "$DELETE_RESP" | grep -oP 'HTTP:\K\d+')

echo "Tentativa de deletar pedido com lancamento 'paid':"
echo "  Status HTTP: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "400" ]; then
    echo "  ✅ Delecao bloqueada (esperado 400)"
else
    echo "  ❌ ERRO - Deveria ter bloqueado com 400"
fi
```

**Resultado esperado:**
- ✅ `400 Bad Request`
- ✅ Mensagem: "Não é possível deletar pedido: lançamento financeiro já está 'paid'..."

---

## TESTE 7: DELETAR PEDIDO COM LANÇAMENTO PENDING (CANCELA AUTOMÁTICO)

### PowerShell

```powershell
# Criar novo pedido
$newOrderResp = curl.exe -s -X POST http://localhost:8000/orders `
  -H "Authorization: Bearer $TOKEN_USER" `
  -H "Content-Type: application/json" `
  -d '{"description":"Pedido para teste delete","total":99.90}' | ConvertFrom-Json

$NEW_ORDER_ID = $newOrderResp.id
Write-Host "Novo pedido criado: $NEW_ORDER_ID"

# Buscar lançamento vinculado
$linkedEntry = (curl.exe -s -X GET "http://localhost:8000/financial/entries?status=pending" `
  -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json).items | 
  Where-Object { $_.order_id -eq $NEW_ORDER_ID }

$LINKED_ENTRY_ID = $linkedEntry.id
Write-Host "Lancamento vinculado: $LINKED_ENTRY_ID (status: $($linkedEntry.status))"

# Deletar pedido
curl.exe -s -X DELETE "http://localhost:8000/orders/$NEW_ORDER_ID" `
  -H "Authorization: Bearer $TOKEN_USER" | Out-Null

Write-Host "Pedido deletado"

# Verificar se lançamento foi cancelado
$canceledEntry = curl.exe -s -X GET "http://localhost:8000/financial/entries/$LINKED_ENTRY_ID" `
  -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json

Write-Host "Status do lancamento apos delete: $($canceledEntry.status)"
```

### Bash

```bash
# Criar novo pedido
NEW_ORDER=$(curl -s -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer $TOKEN_USER" \
  -H "Content-Type: application/json" \
  -d '{"description":"Pedido para teste delete","total":99.90}')

NEW_ORDER_ID=$(echo $NEW_ORDER | jq -r '.id')
echo "Novo pedido criado: $NEW_ORDER_ID"

# Buscar lançamento vinculado (aguardar 1s para garantir criação)
sleep 1
LINKED_ENTRY=$(curl -s -X GET "http://localhost:8000/financial/entries?status=pending" \
  -H "Authorization: Bearer $TOKEN_USER" | jq -r ".items[] | select(.order_id == \"$NEW_ORDER_ID\")")

LINKED_ENTRY_ID=$(echo $LINKED_ENTRY | jq -r '.id')
echo "Lancamento vinculado: $LINKED_ENTRY_ID (status: $(echo $LINKED_ENTRY | jq -r '.status'))"

# Deletar pedido
curl -s -X DELETE "http://localhost:8000/orders/$NEW_ORDER_ID" \
  -H "Authorization: Bearer $TOKEN_USER" > /dev/null

echo "Pedido deletado"

# Verificar se lançamento foi cancelado
CANCELED_STATUS=$(curl -s -X GET "http://localhost:8000/financial/entries/$LINKED_ENTRY_ID" \
  -H "Authorization: Bearer $TOKEN_USER" | jq -r '.status')

echo "Status do lancamento apos delete: $CANCELED_STATUS"
```

**Resultado esperado:**
- ✅ Pedido deletado com sucesso (`204 No Content`)
- ✅ Lançamento vinculado mudou de `pending` → `canceled`

---

## TESTE 8: FILTROS - DATA E KIND

### PowerShell

```powershell
$today = (Get-Date).ToString("yyyy-MM-dd")
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")

# Filtro por data
$dateFiltered = curl.exe -s -X GET "http://localhost:8000/financial/entries?date_from=${yesterday}T00:00:00" `
  -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json

Write-Host "Lancamentos desde ontem: $($dateFiltered.total)"

# Filtro por kind
$revenueOnly = curl.exe -s -X GET "http://localhost:8000/financial/entries?kind=revenue" `
  -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json

$expenseOnly = curl.exe -s -X GET "http://localhost:8000/financial/entries?kind=expense" `
  -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json

Write-Host "Receitas: $($revenueOnly.total)"
Write-Host "Despesas: $($expenseOnly.total)"
```

### Bash

```bash
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# Filtro por data
DATE_FILTERED=$(curl -s -X GET "http://localhost:8000/financial/entries?date_from=${YESTERDAY}T00:00:00" \
  -H "Authorization: Bearer $TOKEN_USER" | jq -r '.total')

echo "Lancamentos desde ontem: $DATE_FILTERED"

# Filtro por kind
REVENUE_ONLY=$(curl -s -X GET "http://localhost:8000/financial/entries?kind=revenue" \
  -H "Authorization: Bearer $TOKEN_USER" | jq -r '.total')

EXPENSE_ONLY=$(curl -s -X GET "http://localhost:8000/financial/entries?kind=expense" \
  -H "Authorization: Bearer $TOKEN_USER" | jq -r '.total')

echo "Receitas: $REVENUE_ONLY"
echo "Despesas: $EXPENSE_ONLY"
```

**Resultado esperado:**
- ✅ Filtros funcionando
- ✅ `date_from` retorna apenas registros >= data
- ✅ `kind=revenue` retorna apenas receitas
- ✅ `kind=expense` retorna apenas despesas

---

## CHECKLIST DE VALIDAÇÃO

- [ ] **TESTE 1:** Login admin e user OK
- [ ] **TESTE 2:** Criar pedido gera lançamento automático (revenue, pending)
- [ ] **TESTE 3:** Multi-tenant: user vê só seus lançamentos, admin vê tudo
- [ ] **TESTE 4:** Criar lançamento manual (expense, order_id=null)
- [ ] **TESTE 5:** Atualizar status pending → paid funciona
- [ ] **TESTE 6:** Deletar pedido com lançamento 'paid' É BLOQUEADO (400)
- [ ] **TESTE 7:** Deletar pedido com lançamento 'pending' CANCELA automaticamente
- [ ] **TESTE 8:** Filtros de data e kind funcionam

---

## SCRIPT COMPLETO (PowerShell)

```powershell
# VALIDACAO COMPLETA ETAPA 3A
# Execute linha por linha ou salve como validate_etapa3a.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VALIDACAO ETAPA 3A - FINANCEIRO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Login
$adminResp = curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@jsp.com&password=123456" | ConvertFrom-Json
$TOKEN_ADMIN = $adminResp.access_token
Write-Host "✅ Admin logado" -ForegroundColor Green

$userResp = curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=user@jsp.com&password=123456" | ConvertFrom-Json
$TOKEN_USER = $userResp.access_token
Write-Host "✅ User logado" -ForegroundColor Green

# 2. Criar pedido e verificar lançamento
$orderResp = curl.exe -s -X POST http://localhost:8000/orders -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d '{"description":"Teste ETAPA 3A","total":350.00}' | ConvertFrom-Json
$ORDER_ID = $orderResp.id
Write-Host "✅ Pedido criado: $ORDER_ID" -ForegroundColor Green

$financialResp = curl.exe -s -X GET "http://localhost:8000/financial/entries?status=pending" -H "Authorization: Bearer $TOKEN_USER" | ConvertFrom-Json
if ($financialResp.total -gt 0) {
    Write-Host "✅ Lancamento automatico criado" -ForegroundColor Green
} else {
    Write-Host "❌ ERRO: Lancamento nao foi criado" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VALIDACAO CONCLUIDA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
```

---

## TROUBLESHOOTING

### Erro: "Module 'app.routers.financial_routes' not found"

**Solução:** Reiniciar uvicorn após adicionar novo módulo.

### Erro: "relation 'core.financial_entries' does not exist"

**Solução:** Executar bootstrap novamente:
```powershell
.\bootstrap_database.ps1
```

### Lançamento não foi criado automaticamente

**Verificar:**
1. `total > 0` no pedido?
2. Logs do uvicorn mostram erro?
3. Tabela `core.financial_entries` existe?

```sql
SELECT * FROM core.financial_entries WHERE order_id = '<order_id>';
```

---

**Data:** 2026-02-15  
**Versão:** 1.0.0 (ETAPA 3A)

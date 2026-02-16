# 🧪 COMANDOS DE TESTE - ETAPA 2

## 📋 Sequência Completa de Testes (PowerShell)

### 1. Bootstrap + Seed
```powershell
# 1. Bootstrap do banco
.\bootstrap_database.ps1

# 2. Criar usuários
python backend\seed_users.py

# 3. Rodar API
cd backend
.\run.ps1
```

---

## 🌐 Testes com cURL (PowerShell)

### 1️⃣ Registrar Novo Usuário
```powershell
curl -X POST http://localhost:8000/auth/register `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"novo@jsp.com\",\"password\":\"senha123\",\"name\":\"Novo Usuario\",\"role\":\"user\"}'
```

### 2️⃣ Login Admin
```powershell
curl -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@jsp.com&password=123456"
```

**Saída esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {...}
}
```

⚠️ **Copie o access_token!**

### 3️⃣ Verificar Usuário Autenticado
```powershell
$token = "SEU_TOKEN_AQUI"

curl -X GET http://localhost:8000/auth/me `
  -H "Authorization: Bearer $token"
```

### 4️⃣ Criar Pedido
```powershell
$token = "SEU_TOKEN_AQUI"

curl -X POST http://localhost:8000/orders `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{\"description\":\"Pedido teste\",\"total\":150.50}'
```

### 5️⃣ Listar Pedidos
```powershell
$token = "SEU_TOKEN_AQUI"

curl -X GET "http://localhost:8000/orders?page=1&page_size=20" `
  -H "Authorization: Bearer $token"
```

### 6️⃣ Deletar Pedido
```powershell
$token = "SEU_TOKEN_AQUI"
$order_id = "uuid-do-pedido"

curl -X DELETE "http://localhost:8000/orders/$order_id" `
  -H "Authorization: Bearer $token"
```

---

## 🧪 Teste Multi-tenant Completo

### Cenário: Admin vs User

```powershell
# 1. Login como ADMIN
$response_admin = curl -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@jsp.com&password=123456" | ConvertFrom-Json

$token_admin = $response_admin.access_token

# 2. Login como USER
$response_user = curl -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=user@jsp.com&password=123456" | ConvertFrom-Json

$token_user = $response_user.access_token

# 3. User cria pedido
curl -X POST http://localhost:8000/orders `
  -H "Authorization: Bearer $token_user" `
  -H "Content-Type: application/json" `
  -d '{\"description\":\"Pedido do user\",\"total\":100}'

# 4. Admin cria pedido
curl -X POST http://localhost:8000/orders `
  -H "Authorization: Bearer $token_admin" `
  -H "Content-Type: application/json" `
  -d '{\"description\":\"Pedido do admin\",\"total\":200}'

# 5. User lista pedidos (vê só os dele)
curl -X GET http://localhost:8000/orders `
  -H "Authorization: Bearer $token_user"

# 6. Admin lista pedidos (vê TODOS)
curl -X GET http://localhost:8000/orders `
  -H "Authorization: Bearer $token_admin"
```

**Resultado esperado:**
- User vê só 1 pedido (dele)
- Admin vê 2 pedidos (todos)

---

## 💡 Script PowerShell Automatizado

Salve como `test_auth.ps1`:

```powershell
# test_auth.ps1 - Teste automatizado da ETAPA 2

Write-Host "🧪 Testando ETAPA 2 - Auth + Permissões" -ForegroundColor Cyan
Write-Host ""

# 1. Login Admin
Write-Host "1️⃣ Login como admin..." -ForegroundColor Yellow
$loginResponse = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/auth/login" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=admin@jsp.com&password=123456"

$token = $loginResponse.access_token
Write-Host "   ✅ Token obtido: $($token.Substring(0,20))..." -ForegroundColor Green
Write-Host ""

# 2. Verificar dados do usuário
Write-Host "2️⃣ Verificando /auth/me..." -ForegroundColor Yellow
$me = Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/auth/me" `
  -Headers @{ Authorization = "Bearer $token" }

Write-Host "   ✅ Autenticado como: $($me.email) | Role: $($me.role)" -ForegroundColor Green
Write-Host ""

# 3. Criar pedido
Write-Host "3️⃣ Criando pedido..." -ForegroundColor Yellow
$order = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/orders" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"description":"Pedido de teste","total":150.50}'

Write-Host "   ✅ Pedido criado: $($order.id)" -ForegroundColor Green
Write-Host ""

# 4. Listar pedidos
Write-Host "4️⃣ Listando pedidos..." -ForegroundColor Yellow
$orders = Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/orders?page=1&page_size=10" `
  -Headers @{ Authorization = "Bearer $token" }

Write-Host "   ✅ Total de pedidos: $($orders.total)" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 Testes concluídos com sucesso!" -ForegroundColor Green
```

**Executar:**
```powershell
.\test_auth.ps1
```

---

## 🔍 Queries SQL Úteis

```sql
-- Ver todos os usuários
SELECT id, name, email, role, is_active 
FROM core.users 
ORDER BY role, email;

-- Ver todos os pedidos com usuário
SELECT 
    o.id,
    o.description,
    o.total,
    u.email as user_email,
    u.role as user_role
FROM core.orders o
JOIN core.users u ON o.user_id = u.id
ORDER BY o.created_at DESC;

-- Contar pedidos por usuário
SELECT 
    u.email,
    u.role,
    COUNT(o.id) as total_pedidos
FROM core.users u
LEFT JOIN core.orders o ON u.id = o.user_id
GROUP BY u.id, u.email, u.role
ORDER BY total_pedidos DESC;

-- Ver últimos logins (se tiver auditoria)
-- (não implementado ainda, mas seria útil)
```

---

## 🏃 Comandos Rápidos

### Rebuild Completo
```powershell
# Derruba tudo e recria
.\bootstrap_database.ps1
python backend\seed_users.py
cd backend
.\run.ps1
```

### Limpar Pedidos (manter usuários)
```sql
DELETE FROM core.orders;
```

### Resetar Senha de Usuário
```python
# Python (dentro do backend/)
from app.database import SessionLocal
from app.models.user import User
from app.auth.security import hash_password
from sqlalchemy import select

db = SessionLocal()
user = db.scalar(select(User).where(User.email == "admin@jsp.com"))
user.password_hash = hash_password("nova_senha")
db.commit()
print("Senha alterada!")
db.close()
```

### Ver Logs da API
```powershell
# A API já tem middleware de logging
# Logs aparecem no console onde você rodou .\run.ps1
```

---

## 📊 Validação Final

### ✅ Checklist
```powershell
# 1. Banco rodando?
docker ps | Select-String "postgres"

# 2. Tabelas criadas?
psql -h localhost -U jsp_user -d jsp_erp -c "\dt core.*"

# 3. Usuários cadastrados?
psql -h localhost -U jsp_user -d jsp_erp -c "SELECT COUNT(*) FROM core.users;"

# 4. API rodando?
curl http://localhost:8000/health

# 5. Swagger acessível?
# Abra: http://localhost:8000/docs
```

---

## 🎯 Casos de Teste Específicos

### Teste 1: Registrar usuário duplicado
```powershell
# Registrar
curl -X POST http://localhost:8000/auth/register `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"teste@jsp.com\",\"password\":\"123456\",\"name\":\"Teste\",\"role\":\"user\"}'

# Tentar registrar novamente (deve dar erro 400)
curl -X POST http://localhost:8000/auth/register `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"teste@jsp.com\",\"password\":\"654321\",\"name\":\"Teste2\",\"role\":\"user\"}'
```

**Resultado esperado:** `{"detail": "E-mail já cadastrado."}`

### Teste 2: Login com senha errada
```powershell
curl -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@jsp.com&password=senha_errada"
```

**Resultado esperado:** `{"detail": "Credenciais inválidas."}`

### Teste 3: Acessar rota sem token
```powershell
curl -X GET http://localhost:8000/orders
```

**Resultado esperado:** `{"detail": "Not authenticated"}`

### Teste 4: Token expirado
```powershell
# Espere 60 minutos ou mude ACCESS_TOKEN_EXPIRE_MINUTES para 1 no .env
# Depois tente usar token antigo
curl -X GET http://localhost:8000/auth/me `
  -H "Authorization: Bearer TOKEN_EXPIRADO"
```

**Resultado esperado:** `{"detail": "Token inválido"}`

---

## 🚀 Performance Test (opcional)

Usando Apache Bench (se instalado):

```bash
# 100 requests, 10 concorrentes
ab -n 100 -c 10 http://localhost:8000/health

# Login test (precisa de arquivo com POST data)
# Criar arquivo login.txt:
# username=admin@jsp.com&password=123456

ab -n 50 -c 5 -p login.txt -T application/x-www-form-urlencoded \
   http://localhost:8000/auth/login
```

---

**Testes completos!** ✅  
Se todos passarem, sua ETAPA 2 está **production-ready**! 🎉

# 🧪 PLANO DE RETESTE - HARDENING COMPLETO

**Versão:** 1.0.0  
**Data:** 15/02/2026  
**Objetivo:** Validar todas as 7 correções de segurança aplicadas

---

## 📋 ÍNDICE DE TESTES

1. [SECRET_KEY Obrigatório](#1-secret_key-obrigatório)
2. [CORS Seguro por Ambiente](#2-cors-seguro-por-ambiente)
3. [Rate Limiting](#3-rate-limiting)
4. [Multi-tenant em GET /orders/{id}](#4-multi-tenant-em-get-ordersid)
5. [Restrição de /auth/users](#5-restrição-de-authusers)
6. [Expiração Unificada](#6-expiração-unificada)
7. [Sanitização de Erros](#7-sanitização-de-erros)

---

## ⚙️ SETUP INICIAL

### 1. Preparar Ambiente

```powershell
# Navegar para backend
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"

# Garantir que banco está rodando
docker ps | Select-String "jsp_postgres"
# Deve mostrar container ativo

# Copiar .env.example e configurar
cp .env.example .env
```

### 2. Configurar .env para Testes

```env
# Desenvolvimento (padrão para testes locais)
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=test-secret-key-change-before-production-minimum-64-chars-long
DATABASE_URL=postgresql+psycopg://admin:admin123@localhost:5432/jsp_erp
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS em development permite localhost
# CORS_ALLOW_ORIGINS não é necessário em development
```

### 3. Instalar Dependências

```powershell
# Instalar slowapi (nova dependência)
pip install slowapi

# Ou atualizar tudo
pip install -r requirements.txt
```

### 4. Iniciar API

```powershell
python -m uvicorn app.main:app --reload
```

**Logs esperados ao iniciar:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Iniciando aplicação em modo: development
INFO:     CORS configurado para origens: ['http://localhost:3000', 'http://localhost:5173']
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 🧪 TESTES

### 1. SECRET_KEY Obrigatório

**Objetivo:** Verificar que API não inicia com SECRET_KEY inválido.

#### Teste 1.1: SECRET_KEY Vazio

```powershell
# Editar .env
# SECRET_KEY=  # (vazio ou comentado)

# Tentar iniciar
python -m uvicorn app.main:app
```

**Resultado esperado:**
```
ValueError: SECRET_KEY não configurado ou usando valor padrão inseguro. 
Configure SECRET_KEY no arquivo .env com uma chave forte (64+ caracteres).
Use: python -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### Teste 1.2: SECRET_KEY Padrão

```powershell
# Editar .env
SECRET_KEY=your-secret-key-change-in-production

# Tentar iniciar
python -m uvicorn app.main:app
```

**Resultado esperado:**
```
ValueError: SECRET_KEY não configurado ou usando valor padrão inseguro...
```

#### Teste 1.3: SECRET_KEY Válido

```powershell
# Gerar chave forte
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Editar .env com chave gerada
SECRET_KEY=<chave-forte-gerada>

# Iniciar
python -m uvicorn app.main:app
```

**Resultado esperado:**
```
INFO:     Started server process...
INFO:     Application startup complete.
✅ API iniciou normalmente
```

---

### 2. CORS Seguro por Ambiente

**Objetivo:** Validar que CORS exige configuração explícita em produção.

#### Teste 2.1: Production sem CORS_ALLOW_ORIGINS

```powershell
# Editar .env
ENVIRONMENT=production
# CORS_ALLOW_ORIGINS=  # (vazio ou comentado)
SECRET_KEY=<chave-forte>

# Tentar iniciar
python -m uvicorn app.main:app
```

**Resultado esperado:**
```
ValueError: CORS_ALLOW_ORIGINS é obrigatório em produção. Configure as origens permitidas separadas por vírgula.
Exemplo: CORS_ALLOW_ORIGINS=https://app.exemplo.com,https://admin.exemplo.com
```

#### Teste 2.2: Production com CORS_ALLOW_ORIGINS

```powershell
# Editar .env
ENVIRONMENT=production
CORS_ALLOW_ORIGINS=https://app.exemplo.com,https://admin.exemplo.com
SECRET_KEY=<chave-forte>

# Iniciar
python -m uvicorn app.main:app
```

**Resultado esperado:**
```
INFO:     Iniciando aplicação em modo: production
INFO:     CORS configurado para origens: ['https://app.exemplo.com', 'https://admin.exemplo.com']
✅ API iniciou normalmente
```

#### Teste 2.3: Development (permite localhost automático)

```powershell
# Editar .env
ENVIRONMENT=development
# CORS_ALLOW_ORIGINS não é necessário
SECRET_KEY=<chave-forte>

# Iniciar
python -m uvicorn app.main:app
```

**Resultado esperado:**
```
INFO:     Iniciando aplicação em modo: development
INFO:     CORS configurado para origens: ['http://localhost:3000', 'http://localhost:5173']
✅ API iniciou normalmente
```

---

### 3. Rate Limiting

**Objetivo:** Validar limites de requisições em /login (5/min) e /register (3/min).

#### Teste 3.1: Rate Limit em POST /auth/login

```powershell
# Fazer 6 tentativas de login em sequência rápida
for ($i=1; $i -le 6; $i++) {
    $response = curl.exe -s -w "\nHTTP_CODE:%{http_code}\n" `
      -X POST http://localhost:8000/auth/login `
      -H "Content-Type: application/x-www-form-urlencoded" `
      -d "username=admin@jsp.com&password=admin123"
    
    Write-Host "`n=== Tentativa $i ===" -ForegroundColor Cyan
    Write-Host $response
    Start-Sleep -Milliseconds 500
}
```

**Resultado esperado:**

**Tentativas 1-5:**
```json
HTTP 200 OK
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Tentativa 6:**
```json
HTTP 429 Too Many Requests
{
  "detail": "Muitas requisições. Tente novamente em alguns instantes.",
  "error": "rate_limit_exceeded"
}
```

**Reset:** Aguardar 60 segundos ou reiniciar API.

#### Teste 3.2: Rate Limit em POST /auth/register

```powershell
# Fazer 4 tentativas de registro em sequência rápida
for ($i=1; $i -le 4; $i++) {
    $response = curl.exe -s -w "\nHTTP_CODE:%{http_code}\n" `
      -X POST http://localhost:8000/auth/register `
      -H "Content-Type: application/json" `
      -d "{\"email\":\"teste$i@jsp.com\",\"password\":\"senha123\",\"full_name\":\"Teste $i\"}"
    
    Write-Host "`n=== Tentativa $i ===" -ForegroundColor Cyan
    Write-Host $response
    Start-Sleep -Milliseconds 500
}
```

**Resultado esperado:**

**Tentativas 1-3:**
```json
HTTP 201 Created
{
  "id": "<uuid>",
  "email": "teste1@jsp.com",
  "full_name": "Teste 1",
  "role": "user"
}
```

**Tentativa 4:**
```json
HTTP 429 Too Many Requests
{
  "detail": "Muitas requisições. Tente novamente em alguns instantes.",
  "error": "rate_limit_exceeded"
}
```

---

### 4. Multi-tenant em GET /orders/{id}

**Objetivo:** Validar que users só veem seus próprios pedidos, admins veem todos.

#### Setup: Criar Tokens

```powershell
# 1️⃣ Login como Admin
$adminLogin = curl.exe -s -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@jsp.com&password=admin123" | ConvertFrom-Json

$TOKEN_ADMIN = $adminLogin.access_token
Write-Host "TOKEN_ADMIN: $TOKEN_ADMIN" -ForegroundColor Green

# 2️⃣ Login como User1 (financeiro@jsp.com)
$user1Login = curl.exe -s -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=financeiro@jsp.com&password=fin123" | ConvertFrom-Json

$TOKEN_USER1 = $user1Login.access_token
Write-Host "TOKEN_USER1: $TOKEN_USER1" -ForegroundColor Green

# 3️⃣ Login como User2 (tecnico@jsp.com)
$user2Login = curl.exe -s -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=tecnico@jsp.com&password=tech123" | ConvertFrom-Json

$TOKEN_USER2 = $user2Login.access_token
Write-Host "TOKEN_USER2: $TOKEN_USER2" -ForegroundColor Green
```

#### Teste 4.1: User1 Cria Pedido

```powershell
$newOrder = curl.exe -s -X POST http://localhost:8000/orders/ `
  -H "Authorization: Bearer $TOKEN_USER1" `
  -H "Content-Type: application/json" `
  -d '{"product_name":"Laptop","quantity":2,"unit_price":3500.00}' | ConvertFrom-Json

$ORDER_ID = $newOrder.id
Write-Host "Pedido criado - ID: $ORDER_ID" -ForegroundColor Yellow
Write-Host "User ID do pedido: $($newOrder.user_id)" -ForegroundColor Yellow
```

**Response esperado:**
```json
HTTP 201 Created
{
  "id": "<order-uuid>",
  "user_id": "<user1-uuid>",
  "product_name": "Laptop",
  "quantity": 2,
  "unit_price": 3500.00,
  "total_price": 7000.00,
  "status": "pending"
}
```

#### Teste 4.2: User1 Acessa Seu Próprio Pedido (✅ Permitido)

```powershell
curl.exe -s -X GET "http://localhost:8000/orders/$ORDER_ID" `
  -H "Authorization: Bearer $TOKEN_USER1"
```

**Response esperado:**
```json
HTTP 200 OK
{
  "id": "<order-uuid>",
  "user_id": "<user1-uuid>",
  "product_name": "Laptop",
  ...
}
✅ Sucesso
```

#### Teste 4.3: User2 Tenta Acessar Pedido de User1 (❌ Bloqueado)

```powershell
curl.exe -s -w "\nHTTP_CODE:%{http_code}\n" `
  -X GET "http://localhost:8000/orders/$ORDER_ID" `
  -H "Authorization: Bearer $TOKEN_USER2"
```

**Response esperado:**
```json
HTTP 404 Not Found
{
  "detail": "Pedido <order-uuid> não encontrado"
}
❌ Bloqueado (retorna 404, não 403, para não revelar existência)
```

#### Teste 4.4: Admin Acessa Pedido de User1 (✅ Permitido)

```powershell
curl.exe -s -X GET "http://localhost:8000/orders/$ORDER_ID" `
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

**Response esperado:**
```json
HTTP 200 OK
{
  "id": "<order-uuid>",
  "user_id": "<user1-uuid>",
  "product_name": "Laptop",
  ...
}
✅ Admin vê qualquer pedido
```

---

### 5. Restrição de /auth/users

**Objetivo:** Validar que apenas admins podem listar usuários.

#### Teste 5.1: User Comum Tenta Listar (❌ Bloqueado)

```powershell
curl.exe -s -w "\nHTTP_CODE:%{http_code}\n" `
  -X GET http://localhost:8000/auth/users `
  -H "Authorization: Bearer $TOKEN_USER1"
```

**Response esperado:**
```json
HTTP 403 Forbidden
{
  "detail": "Acesso negado. Apenas administradores podem listar usuários."
}
❌ Bloqueado
```

#### Teste 5.2: Admin Lista Usuários (✅ Permitido)

```powershell
curl.exe -s -X GET http://localhost:8000/auth/users `
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

**Response esperado:**
```json
HTTP 200 OK
[
  {
    "id": "<uuid>",
    "email": "admin@jsp.com",
    "full_name": "Administrador",
    "role": "admin",
    "is_active": true
  },
  {
    "id": "<uuid>",
    "email": "financeiro@jsp.com",
    "full_name": "Financeiro",
    "role": "finance",
    "is_active": true
  },
  ...
]
✅ Sucesso
```

---

### 6. Expiração Unificada

**Objetivo:** Validar que token expira conforme ACCESS_TOKEN_EXPIRE_MINUTES.

#### Teste 6.1: Configurar Expiração Curta

```powershell
# Editar .env
ACCESS_TOKEN_EXPIRE_MINUTES=1  # 1 minuto

# Reiniciar API
```

#### Teste 6.2: Gerar Token e Aguardar Expiração

```powershell
# Fazer login
$login = curl.exe -s -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@jsp.com&password=admin123" | ConvertFrom-Json

$TOKEN = $login.access_token

# Usar imediatamente (deve funcionar)
curl.exe -s -X GET http://localhost:8000/auth/me `
  -H "Authorization: Bearer $TOKEN"

Write-Host "Aguardando 70 segundos para expiração..." -ForegroundColor Yellow
Start-Sleep -Seconds 70

# Usar após expiração (deve falhar)
curl.exe -s -w "\nHTTP_CODE:%{http_code}\n" `
  -X GET http://localhost:8000/auth/me `
  -H "Authorization: Bearer $TOKEN"
```

**Response esperado após expiração:**
```json
HTTP 401 Unauthorized
{
  "detail": "Token expirado ou inválido"
}
✅ Token expirou conforme configurado
```

**Restaurar configuração:**
```env
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

### 7. Sanitização de Erros

**Objetivo:** Validar que erros são genéricos em produção, detalhados em dev.

#### Teste 7.1: Erro em Development (DEBUG=True)

```powershell
# Editar .env
ENVIRONMENT=development
DEBUG=True

# Reiniciar API

# Fazer request com UUID inválido
curl.exe -s -w "\nHTTP_CODE:%{http_code}\n" `
  -X GET http://localhost:8000/orders/invalid-uuid `
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

**Response esperado:**
```json
HTTP 500 Internal Server Error
{
  "detail": "Erro ao buscar pedido: invalid input syntax for type uuid: \"invalid-uuid\""
}
✅ Erro detalhado em desenvolvimento
```

#### Teste 7.2: Erro em Production (DEBUG=False)

```powershell
# Editar .env
ENVIRONMENT=production
DEBUG=False
CORS_ALLOW_ORIGINS=http://localhost:3000

# Reiniciar API

# Fazer mesmo request
curl.exe -s -w "\nHTTP_CODE:%{http_code}\n" `
  -X GET http://localhost:8000/orders/invalid-uuid `
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

**Response esperado:**
```json
HTTP 500 Internal Server Error
{
  "detail": "Erro ao buscar pedido"
}
✅ Erro genérico em produção (sem revelar detalhes técnicos)
```

**Logs (backend):**
```
ERROR - Erro ao buscar pedido: invalid input syntax for type uuid: "invalid-uuid"
Traceback (most recent call last):
  ...
✅ Detalhes completos ficam apenas nos logs
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Após executar todos os testes, verificar:

```
[ ] 1. API não inicia com SECRET_KEY vazio ou padrão
[ ] 2. API não inicia em production sem CORS_ALLOW_ORIGINS
[ ] 3. API permite localhost em development sem CORS_ALLOW_ORIGINS
[ ] 4. Rate limiting funciona: 5/min em /login, 3/min em /register
[ ] 5. Response 429 contém mensagem de rate limit e erro formatado
[ ] 6. GET /orders/{id} retorna 404 quando user tenta acessar pedido de outro
[ ] 7. GET /orders/{id} permite admin acessar qualquer pedido
[ ] 8. GET /auth/users retorna 403 para user comum
[ ] 9. GET /auth/users permite admin listar usuários
[ ] 10. Token expira conforme ACCESS_TOKEN_EXPIRE_MINUTES
[ ] 11. Erros detalhados em development (DEBUG=True)
[ ] 12. Erros genéricos em production (DEBUG=False)
[ ] 13. Logs contem stack trace completo mesmo em production
```

---

## 🔧 TROUBLESHOOTING

### Problema: Rate Limit não funciona

**Diagnóstico:**
```powershell
# Verificar se slowapi está instalado
pip show slowapi
```

**Solução:**
```powershell
pip install slowapi
```

### Problema: Token não expira

**Diagnóstico:**
```powershell
# Verificar horário do servidor
python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc))"

# Decodificar token (sem validar)
python -c "import jwt, sys; print(jwt.decode(sys.argv[1], options={'verify_signature': False}))" "<token>"
```

**Campo `exp` esperado:**
```json
{
  "sub": "<user-id>",
  "exp": 1739232000  # Deve ser timestamp + ACCESS_TOKEN_EXPIRE_MINUTES
}
```

### Problema: CORS bloqueando em desenvolvimento

**Diagnóstico:**
```powershell
# Verificar configuração
curl.exe -s -X OPTIONS http://localhost:8000/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
```

**Response esperado:**
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: POST
```

---

## 📊 RELATÓRIO DE TESTES

**Template para documentar resultados:**

| # | Teste | Status | Observações |
|---|-------|--------|-------------|
| 1.1 | SECRET_KEY vazio | ✅ / ❌ | |
| 1.2 | SECRET_KEY padrão | ✅ / ❌ | |
| 1.3 | SECRET_KEY válido | ✅ / ❌ | |
| 2.1 | CORS prod sem config | ✅ / ❌ | |
| 2.2 | CORS prod com config | ✅ / ❌ | |
| 2.3 | CORS dev (localhost) | ✅ / ❌ | |
| 3.1 | Rate limit /login | ✅ / ❌ | |
| 3.2 | Rate limit /register | ✅ / ❌ | |
| 4.1 | User1 cria pedido | ✅ / ❌ | |
| 4.2 | User1 acessa próprio | ✅ / ❌ | |
| 4.3 | User2 bloqueado | ✅ / ❌ | |
| 4.4 | Admin acessa qualquer | ✅ / ❌ | |
| 5.1 | User bloqueado em /users | ✅ / ❌ | |
| 5.2 | Admin acessa /users | ✅ / ❌ | |
| 6.1 | Token expira | ✅ / ❌ | |
| 7.1 | Erro detalhado (dev) | ✅ / ❌ | |
| 7.2 | Erro genérico (prod) | ✅ / ❌ | |

---

**Todos os testes passando = Sistema production-ready!** 🚀

**Próximo passo:** Deploy em ambiente staging para validação final.

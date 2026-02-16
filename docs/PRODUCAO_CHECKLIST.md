# ✅ CHECKLIST DE PRODUÇÃO - ERP JSP

**Versão:** 1.0.0 (Hardened)  
**Data:** 15/02/2026  
**Status:** Production-Ready após aplicação de todas as correções

---

## 🚨 VARIÁVEIS OBRIGATÓRIAS

Antes de fazer deploy em produção, configure estas variáveis no `.env`:

### 1️⃣ ENVIRONMENT

```bash
ENVIRONMENT=production
```

**Valores válidos:**
- `development` - Desenvolvimento local
- `production` - Produção

⚠️ **Crítico:** Define comportamento de CORS, mensagens de erro e validações.

---

### 2️⃣ SECRET_KEY

```bash
SECRET_KEY=<sua-chave-secreta-forte>
```

**Como gerar uma chave forte:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Saída exemplo:**
```
9vZp8K3mN2xR7wQ1sT4yU6bH5jL0aF9dG8cV2nM3kP1oE4iW7qZ6tY5uR8xS
```

⚠️ **Crítico:**
- **NUNCA** usar valor padrão (`your-secret-key-change-in-production`)
- **NUNCA** commitar no Git
- Mínimo 64 caracteres
- Usar secrets manager em produção (AWS Secrets Manager, Azure Key Vault, etc.)

**Validação:**
```bash
# A aplicação NÃO iniciará se SECRET_KEY estiver:
# - Vazio
# - Com valor padrão 'your-secret-key-change-in-production'
```

---

### 3️⃣ CORS_ALLOW_ORIGINS

```bash
CORS_ALLOW_ORIGINS=https://app.exemplo.com,https://admin.exemplo.com
```

**Formato:**
- Lista de URLs separadas por vírgula (SEM espaços)
- SEMPRE usar HTTPS em produção
- Especificar domínios exatos (nunca `*`)

**Exemplos:**

✅ **Correto:**
```bash
CORS_ALLOW_ORIGINS=https://erp.minhaempresa.com,https://app.minhaempresa.com
```

❌ **ERRADO:**
```bash
CORS_ALLOW_ORIGINS=*  # NUNCA em produção!
CORS_ALLOW_ORIGINS=http://exemplo.com  # Usar HTTPS
CORS_ALLOW_ORIGINS=https://exemplo.com, https://outro.com  # Sem espaços!
```

⚠️ **Crítico:**
- Aplicação **FALHARÁ AO INICIAR** se vazio em produção
- `allow_origins=["*"]` não é permitido com `allow_credentials=True`

---

### 4️⃣ DATABASE_URL

```bash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

**Exemplo produção:**
```bash
DATABASE_URL=postgresql+psycopg://jsp_prod:SENHA_FORTE@db.exemplo.com:5432/jsp_erp_prod
```

⚠️ **Segurança:**
- Usar usuário dedicado (não `postgres`)
- Senha forte (16+ caracteres)
- Conexão SSL em produção (adicionar `?sslmode=require`)

---

### 5️⃣ DEBUG

```bash
DEBUG=False
```

⚠️ **Crítico:**
- **SEMPRE** `False` em produção
- `True` expõe stack traces, variáveis e informações sensíveis

---

## 🔒 HARDENING APLICADO

### ✅ 1. SECRET_KEY Obrigatório

**Antes:**
```python
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")  # ❌
```

**Depois:**
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production":
    raise ValueError("SECRET_KEY não configurado ou usando valor padrão inseguro...")  # ✅
```

---

### ✅ 2. CORS Seguro por Ambiente

**Antes:**
```python
allow_origins=["*"]  # ❌ Inseguro
allow_credentials=True
```

**Depois:**
```python
# Em development: permite localhost
# Em production: exige CORS_ALLOW_ORIGINS configurado
allow_origins=CORS_ALLOW_ORIGINS  # Lista específica
allow_credentials=True  # Apenas se origins != ["*"]
```

**Validação em produção:**
```python
if ENVIRONMENT == "production" and not CORS_ALLOW_ORIGINS:
    raise ValueError("CORS_ALLOW_ORIGINS é obrigatório em produção")
```

---

### ✅ 3. Rate Limiting

**Limiter global:** 100 requisições/minuto por IP (todos os endpoints)

**Endpoints com limites específicos (mais restritivos):**

| Endpoint | Limite | Motivo |
|----------|--------|--------|
| `POST /auth/login` | 5/min por IP | Prevenir brute force |
| `POST /auth/register` | 3/min por IP | Prevenir spam/enumeração |

**Tecnologia:** slowapi (baseado em Flask-Limiter)

**Response quando excedido:**
```json
HTTP 429 Too Many Requests
{
  "detail": "Muitas requisições. Tente novamente em alguns instantes.",
  "error": "rate_limit_exceeded"
}
```

**⚠️ Atenção:**
- O limite global (100/min) pode impactar testes em massa ou uso intensivo do Swagger
- Em produção, monitorar logs de rate limit para ajustar limites se necessário
- Limites específicos (5/min login, 3/min register) prevalecem sobre o limite global

---

### ✅ 4. Multi-tenant em GET /orders/{id}

**Antes:**
```python
def get_order(order_id: UUID, db: Session):
    order = OrderService.get_order(db, order_id)
    return order  # ❌ Qualquer user pode ver qualquer pedido
```

**Depois:**
```python
def get_order(order_id: UUID, current_user: User, db: Session):
    order = OrderService.get_order(db, order_id)
    
    # Validação multi-tenant
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(404, detail="Pedido não encontrado")  # ✅
```

**Comportamento:**
- **Admin:** vê qualquer pedido
- **User/Tech/Finance:** vê APENAS seus próprios pedidos
- Retorna `404` (não `403`) para não revelar existência do pedido

**⚠️ Decisão de segurança:**
Retornamos 404 em vez de 403 quando um usuário não-admin tenta acessar pedido de terceiro.
Isso evita que atacantes descubram quais IDs de pedidos existem no sistema (information disclosure).
Exemplo: Se retornasse 403, um atacante saberia que o pedido existe mas não tem acesso.
Com 404, não é possível distinguir se o pedido não existe ou se não tem permissão.

---

### ✅ 5. Restrição de /auth/users

**Antes:**
```python
@router.get("/users")
def list_users(current_user: User, db: Session):
    return UserRepository.get_all_active(db)  # ❌ Qualquer user pode listar
```

**Depois:**
```python
@router.get("/users")
def list_users(current_user: User, db: Session):
    if current_user.role != "admin":
        raise HTTPException(403, detail="Acesso negado. Apenas administradores.")  # ✅
    return UserRepository.get_all_active(db)
```

---

### ✅ 6. Expiração Unificada

**Antes:**
```python
# config.py
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# auth/router.py
access_token = create_access_token(subject=user.id, expires_minutes=60)  # ❌ Hardcoded
```

**Depois:**
```python
# config.py
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# auth/router.py
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
access_token = create_access_token(subject=user.id, expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # ✅
```

---

### ✅ 7. Sanitização de Erros em Produção

**Antes:**
```python
except Exception as e:
    raise HTTPException(500, detail=f"Erro: {str(e)}")  # ❌ Vaza stack trace
```

**Depois:**
```python
from app.core.errors import sanitize_error_message

except Exception as e:
    detail = sanitize_error_message(e, "Erro ao processar pedido")  # ✅
    raise HTTPException(500, detail=detail)
```

**Comportamento:**
- **Development/DEBUG=True:** Retorna `"Erro ao processar pedido: <detalhes>"`
- **Production/DEBUG=False:** Retorna apenas `"Erro ao processar pedido"`
- **Sempre** loga erro completo com `logger.error(..., exc_info=True)`

---

## 🧪 TESTES DE VALIDAÇÃO

### 1. Validar SECRET_KEY

```bash
# Remover SECRET_KEY do .env
# Tentar iniciar API

cd backend
python -m uvicorn app.main:app

# ✅ Deve FALHAR com:
# ValueError: SECRET_KEY não configurado ou usando valor padrão inseguro...
```

---

### 2. Validar CORS em Produção

**Configurar:**
```bash
ENVIRONMENT=production
CORS_ALLOW_ORIGINS=  # Vazio
```

**Resultado esperado:**
```
ValueError: CORS_ALLOW_ORIGINS é obrigatório em produção...
```

**Teste correto:**
```bash
ENVIRONMENT=production
CORS_ALLOW_ORIGINS=https://app.exemplo.com
```

API deve iniciar normalmente.

---

### 3. Testar Rate Limiting

**Login (5/minuto):**

```powershell
# Fazer 6 tentativas de login em 1 minuto
for ($i=1; $i -le 6; $i++) {
    curl -X POST http://localhost:8000/auth/login `
      -H "Content-Type: application/x-www-form-urlencoded" `
      -d "username=admin@jsp.com&password=123456"
    Write-Host "Tentativa $i"
}
```

**Resultado esperado:**
- Tentativas 1-5: `200 OK` (ou `401` se senha errada)
- Tentativa 6+: `429 Too Many Requests`

**Response da 6ª tentativa:**
```json
{
  "detail": "Muitas requisições. Tente novamente em alguns instantes.",
  "error": "rate_limit_exceeded"
}
```

---

### 4. Testar Multi-tenant em GET /orders/{id}

**Setup:**
```bash
# 1. Login como user1
TOKEN_USER1=<token>

# 2. User1 cria pedido
ORDER_ID=<uuid>

# 3. Login como user2
TOKEN_USER2=<token>
```

**Teste:**
```bash
# User2 tenta acessar pedido de User1
curl -X GET http://localhost:8000/orders/$ORDER_ID `
  -H "Authorization: Bearer $TOKEN_USER2"
```

**Resultado esperado:**
```json
HTTP 404 Not Found
{
  "detail": "Pedido <uuid> não encontrado"
}
```

**Admin acessa:**
```bash
# Admin pode ver qualquer pedido
curl -X GET http://localhost:8000/orders/$ORDER_ID `
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

**Resultado esperado:**
```json
HTTP 200 OK
{
  "id": "<uuid>",
  "user_id": "<user1_id>",
  ...
}
```

---

### 5. Testar Restrição de /auth/users

**User comum:**
```bash
curl -X GET http://localhost:8000/auth/users `
  -H "Authorization: Bearer $TOKEN_USER"
```

**Resultado esperado:**
```json
HTTP 403 Forbidden
{
  "detail": "Acesso negado. Apenas administradores podem listar usuários."
}
```

**Admin:**
```bash
curl -X GET http://localhost:8000/auth/users `
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

**Resultado esperado:**
```json
HTTP 200 OK
[
  {"id": "...", "email": "admin@jsp.com", "role": "admin", ...},
  {"id": "...", "email": "user@jsp.com", "role": "user", ...}
]
```

---

### 6. Testar Sanitização de Erros

**Em development (DEBUG=True):**
```bash
# Fazer request que gere erro interno
# Exemplo: pedido com UUID inválido

curl http://localhost:8000/orders/invalid-uuid
```

**Response esperado:**
```json
{
  "detail": "Erro: invalid input syntax for type uuid: \"invalid-uuid\""  # ✅ Detalhes
}
```

**Em production (DEBUG=False):**
```bash
ENVIRONMENT=production
DEBUG=False
```

**Response esperado:**
```json
{
  "detail": "Erro ao buscar pedido"  # ✅ Apenas mensagem genérica
}
```

---

## 📝 CHECKLIST PRÉ-DEPLOY

```
[ ] 1. Configurar ENVIRONMENT=production
[ ] 2. Gerar e configurar SECRET_KEY forte (64+ chars)
[ ] 3. Configurar CORS_ALLOW_ORIGINS com domínios exatos
[ ] 4. Configurar DATABASE_URL com usuário dedicado e SSL
[ ] 5. Configurar DEBUG=False
[ ] 6. Testar que API não inicia com SECRET_KEY vazio
[ ] 7. Testar que API não inicia com CORS_ALLOW_ORIGINS vazio em production
[ ] 8. Validar rate limiting (login 5/min, register 3/min)
[ ] 9. Validar multi-tenant em GET /orders/{id}
[ ] 10. Validar /auth/users bloqueado para não-admin
[ ] 11. Validar mensagens de erro genéricas (sem stack traces)
[ ] 12. Fazer backup do banco antes do deploy
[ ] 13. Configurar monitoramento (logs, métricas, alertas)
[ ] 14. Configurar SSL/TLS (HTTPS obrigatório)
[ ] 15. Configurar firewall (apenas portas necessárias)
```

---

## 🚀 DEPLOY SEGURO

### Variáveis de Ambiente em Servidores

**Não use .env em produção!** Use:

- **AWS:** Parameter Store / Secrets Manager
- **Azure:** Key Vault
- **GCP:** Secret Manager
- **Heroku:** Config Vars
- **Docker:** Secrets / Environment

### Exemplo Docker Compose (Produção):

```yaml
version: '3.8'

services:
  api:
    image: jsp-erp-api:latest
    environment:
      ENVIRONMENT: production
      DEBUG: "False"
    secrets:
      - secret_key
      - database_url
      - cors_origins
    ports:
      - "8000:8000"

secrets:
  secret_key:
    external: true
  database_url:
    external: true
  cors_origins:
    external: true
```

---

## 🔐 BOAS PRÁTICAS ADICIONAIS

### 1. HTTPS Obrigatório

```nginx
# Nginx - Redirecionar HTTP → HTTPS
server {
    listen 80;
    server_name api.exemplo.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.exemplo.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Logs Estruturados

- Usar logging JSON em produção
- Não logar senhas, tokens ou dados sensíveis
- Monitorar logs de rate limiting

### 3. Monitoramento

- **APM:** New Relic, Datadog, Sentry
- **Alertas:** Rate limit excedido, erros 500, tentativas de login falhadas

### 4. Backup

- Backup automático do banco (diário mínimo)
- Testar restore periodicamente
- Backup de secrets (criptografado)

---

## 📊 MÉTRICAS DE SUCESSO

Após deploy em produção, validar:

- ✅ Zero erros 500 por secrets inválidos
- ✅ Rate limiting funcionando (429 nos logs)
- ✅ Multi-tenant funcionando (404 para acessos indevidos)
- ✅ /auth/users bloqueado (403 nos logs)
- ✅ CORS rejeitando origins não autorizadas
- ✅ Tempo de resposta < 200ms (p95)

---

## 🆘 TROUBLESHOOTING

### Erro: "SECRET_KEY não configurado"

**Solução:**
```bash
# Gerar chave
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Adicionar ao .env
echo "SECRET_KEY=<chave-gerada>" >> .env
```

### Erro: "CORS_ALLOW_ORIGINS é obrigatório em produção"

**Solução:**
```bash
# Adicionar ao .env
echo "CORS_ALLOW_ORIGINS=https://app.exemplo.com" >> .env
```

### Rate Limit Muito Restritivo

**Ajustar limites:**

```python
# app/auth/router.py
@limiter.limit("10/minute")  # Era 5/minute
def login(...):
    ...
```

---

**Sistema production-ready após aplicação de todas as correções!** ✅

**Próximas melhorias (opcional):**
- Refresh tokens
- 2FA (two-factor authentication)
- Auditoria de ações
- WAF (Web Application Firewall)

# Deploy Staging - ERP JSP Backend

Guia para deploy do backend FastAPI em ambiente de staging (Render, Railway, Fly.io, etc.).

---

## 📋 Variáveis de Ambiente Obrigatórias

### Core

```bash
# Ambiente (aceita: local, development, production, test)
ENV=production

# Banco de dados PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Segurança - JWT (OBRIGATÓRIO, NÃO usar valor padrão)
SECRET_KEY=<gere_com_comando_abaixo>

# CORS - origens permitidas (CSV)
CORS_ALLOW_ORIGINS=https://seu-frontend.com,https://app.exemplo.com
```

### Opcionais

```bash
# Debug mode (default: false)
DEBUG=false

# Expiração do token JWT em minutos (default: 60)
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## 🔑 Gerar SECRET_KEY Segura

Execute localmente antes do deploy:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Exemplo de output:**
```
XyZ1_AbC2-DeF3_GhI4-JkL5_MnO6-PqR7_StU8-VwX9_YzA0-BcD1_EfG2-HiJ3_KlM4
```

⚠️ **NUNCA** commitar esta chave no Git ou usar valor padrão!

---

## 🚀 Comando de Inicialização

### Produção (Render/Railway/Fly.io)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Local (desenvolvimento)

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## ✅ Validação Pós-Deploy

### 1. Health Check

Teste se a aplicação subiu corretamente:

```bash
curl https://seu-app.onrender.com/health
```

**Resposta esperada:**
```json
{
  "ok": true,
  "service": "jsp_erp",
  "env": "production",
  "app": "ERP JSP",
  "version": "1.0.0",
  "database": "healthy"
}
```

✅ **Checklist:**
- `ok: true` → Banco de dados está respondendo
- `env: "production"` → Ambiente correto
- `database: "healthy"` → Conexão ao PostgreSQL OK

---

### 2. Teste de Autenticação

#### a) Criar usuário (se necessário)

```bash
curl -X POST https://seu-app.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@exemplo.com",
    "password": "SenhaForte123!",
    "full_name": "Admin Staging"
  }'
```

**Resposta esperada (201):**
```json
{
  "id": "uuid-aqui",
  "email": "admin@exemplo.com",
  "full_name": "Admin Staging",
  "role": "user",
  "created_at": "2026-02-23T12:00:00"
}
```

#### b) Login

```bash
curl -X POST https://seu-app.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@exemplo.com",
    "password": "SenhaForte123!"
  }'
```

**Resposta esperada (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### c) Testar endpoint autenticado

```bash
TOKEN="<access_token_do_passo_anterior>"

curl https://seu-app.onrender.com/users/me \
  -H "Authorization: Bearer $TOKEN"
```

**Resposta esperada (200):**
```json
{
  "id": "uuid-aqui",
  "email": "admin@exemplo.com",
  "full_name": "Admin Staging",
  "role": "user"
}
```

---

## 🐳 Configuração Render (exemplo)

### Opção 1: Web Service GUI

1. **New** → **Web Service**
2. **Build Command:**
   ```bash
   cd backend && pip install -r requirements.txt
   ```
3. **Start Command:**
   ```bash
   cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
   ```
4. **Environment Variables:**
   - `ENV` = `production`
   - `DATABASE_URL` = (adicionar PostgreSQL database)
   - `SECRET_KEY` = (gerar com comando acima)
   - `CORS_ALLOW_ORIGINS` = `https://seu-frontend.onrender.com`

### Opção 2: render.yaml (IaC)

Crie `render.yaml` na raiz do projeto:

```yaml
services:
  - type: web
    name: jsp-erp-backend
    env: python
    region: oregon
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
    envVars:
      - key: ENV
        value: production
      - key: SECRET_KEY
        generateValue: true  # Render gera automaticamente
      - key: CORS_ALLOW_ORIGINS
        value: https://seu-frontend.onrender.com
      - key: DATABASE_URL
        fromDatabase:
          name: jsp-erp-db
          property: connectionString

databases:
  - name: jsp-erp-db
    databaseName: jsp_erp_production
    user: jsp_user
    region: oregon
```

---

## 🔒 Checklist de Segurança

Antes de ir para produção:

- [ ] `SECRET_KEY` gerada aleatoriamente (não usar padrão)
- [ ] `ENV=production` configurado
- [ ] `CORS_ALLOW_ORIGINS` com domínios específicos (NUNCA `*` em produção)
- [ ] `DATABASE_URL` usando SSL (`?sslmode=require`)
- [ ] `DEBUG=false` (ou omitir, padrão é false)
- [ ] Credenciais do banco em variáveis de ambiente (não hardcoded)
- [ ] Health check `/health` retornando `ok: true`
- [ ] Logs não vazando secrets ou passwords

---

## 📊 Monitoramento

### Logs no Render

```bash
render logs -s jsp-erp-backend --tail 100
```

### Logs de Startup (verificar)

Ao iniciar, deve aparecer:

```
🚀 ERP JSP v1.0.0 iniciado
📍 Environment: production
🔒 CORS origins: ['https://seu-frontend.com']
🐛 Debug mode: False
✅ Database connection: OK
```

❌ **Se aparecer:**
```
❌ Database connection: FAILED - could not connect to server
```
→ Verificar `DATABASE_URL` e conectividade ao PostgreSQL

---

## 🗄️ Migrations

### Aplicar migrations antes do primeiro deploy:

```bash
# Localmente, apontando para DB de staging
export DATABASE_URL="postgresql://user:pass@staging-db-host:5432/dbname"

cd backend
alembic upgrade head
```

Ou configure no **Build Command** do Render:

```bash
cd backend && pip install -r requirements.txt && alembic upgrade head
```

---

## 🚨 Troubleshooting

### Erro: "SECRET_KEY não configurado"

**Causa:** Variável `SECRET_KEY` não definida ou usando valor padrão.

**Solução:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Copiar output e setar em Environment Variables
```

---

### Erro: "CORS_ALLOW_ORIGINS é obrigatório em produção"

**Causa:** `ENV=production` mas `CORS_ALLOW_ORIGINS` vazio.

**Solução:**
```bash
# No Render/Railway:
CORS_ALLOW_ORIGINS=https://seu-frontend.com,https://app.exemplo.com
```

---

### Health check retorna `ok: false`

**Causa:** Banco de dados inacessível.

**Diagnóstico:**
```bash
curl https://seu-app.onrender.com/health | jq
```

Se `database: "unhealthy: ..."`, verificar:
1. `DATABASE_URL` correta
2. PostgreSQL rodando e acessível
3. Firewall/network permissions
4. Migrations aplicadas (`alembic upgrade head`)

---

## 📚 Documentação Adicional

- **API Docs (Swagger):** `https://seu-app.onrender.com/docs`
- **ReDoc:** `https://seu-app.onrender.com/redoc`
- **OpenAPI JSON:** `https://seu-app.onrender.com/openapi.json`

---

## 🎯 Próximos Passos

Após validar staging:

1. Configurar monitoring (Sentry, DataDog, etc.)
2. Configurar rate limiting customizado
3. Adicionar Redis para cache (opcional)
4. Configurar backups automáticos do PostgreSQL
5. Implementar CI/CD com GitHub Actions
6. Configurar health checks periódicos no Render

---

**Última atualização:** 2026-02-23  
**Versão:** 1.0.0  
**Contato:** juliano.saroba@exemplo.com

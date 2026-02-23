# Deploy Staging/Production - ERP JSP Backend

Guia completo para deploy do backend FastAPI no **Render.com** (recomendado).

> ✨ **Deploy em 5 minutos** usando Infrastructure as Code (render.yaml)

---

## 📋 Índice

1. [Pré-requisitos](#-pré-requisitos)
2. [Deploy via Render Blueprint (Recomendado)](#-deploy-via-render-blueprint-recomendado)
3. [Deploy Manual via Dashboard](#-deploy-manual-via-dashboard-alternativo)
4. [Variáveis de Ambiente](#-variáveis-de-ambiente)
5. [Migrations Automáticas](#-migrations-automáticas-alembic)
6. [Validação Pós-Deploy](#-validação-pós-deploy)
7. [Smoke Test Completo](#-smoke-test-completo)
8. [Troubleshooting](#-troubleshooting)
9. [Custos e Planos](#-custos-e-planos)

---

## 🎯 Pré-requisitos

- ✅ Conta no GitHub com repositório do projeto
- ✅ Conta no [Render.com](https://render.com) (gratuita)
- ✅ Python 3.11+ instalado localmente (para smoke test)
- ✅ Git configurado
- ✅ Código commitado e pushed para `master` branch

---

## 🚀 Deploy via Render Blueprint (Recomendado)

**Vantagens:**
- ✨ Deploy em **um clique**
- 🔄 Automatic deployments on git push
- 🗄️ Database provisionada automaticamente
- 🔑 SECRET_KEY gerada automaticamente
- 🔗 DATABASE_URL linkada automaticamente
- 📊 Health check configurado

### Passo 1: Verificar render.yaml

O arquivo `render.yaml` na raiz do projeto define toda a infraestrutura:

```yaml
services:
  - type: web
    name: jsp-erp-backend
    runtime: python
    region: oregon
    plan: starter  # $7/mês (ou free com limitações)
    branch: master
    rootDir: backend
    
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
      chmod +x ../scripts/render_release.sh
      ../scripts/render_release.sh
    
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
    
    healthCheckPath: /health
    
    envVars:
      - key: ENV
        value: production
      
      - key: SECRET_KEY
        generateValue: true  # Render gera automaticamente!
        sync: false
      
      - key: CORS_ALLOW_ORIGINS
        value: https://seu-frontend.onrender.com  # ⚠️ ALTERE ISSO
      
      - key: DATABASE_URL
        fromDatabase:
          name: jsp-erp-db
          property: connectionString

databases:
  - name: jsp-erp-db
    databaseName: jsp_erp_production
    user: jsp_user
    region: oregon
    plan: starter  # $7/mês (ou free com 90 dias)
```

⚠️ **IMPORTANTE:** Altere `CORS_ALLOW_ORIGINS` para o domínio real do seu frontend!

### Passo 2: Push para GitHub

```bash
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'

# Verificar status
git status

# Commitar qualquer alteração pendente
git add -A
git commit -m "chore: Prepare for Render deployment"

# Push para master
git push origin master
```

### Passo 3: Deploy no Render Dashboard

#### 3.1 - Acessar Dashboard

1. Acesse [https://dashboard.render.com](https://dashboard.render.com)
2. Login com GitHub
3. Clique em **New** → **Blueprint**

#### 3.2 - Conectar Repositório

1. **Connect a repository:** Selecione `JulianoSaroba123/jsp_erp` (ou seu fork)
2. **Blueprint Name:** Deixe padrão (`jsp_erp`)
3. **Blueprint file:** `render.yaml` (auto-detectado ✅)

#### 3.3 - Revisar Serviços

O Render mostrará:

**Web Services:**
- 🌐 **jsp-erp-backend**
  - Type: Web Service
  - Region: Oregon
  - Plan: Starter ($7/month)
  - Python Runtime

**Databases:**
- 🗄️ **jsp-erp-db**
  - Type: PostgreSQL 16
  - Region: Oregon
  - Plan: Starter ($7/month)
  - Database Name: `jsp_erp_production`

**Total: ~$14/month** (ou free tier - veja seção [Custos](#-custos-e-planos))

#### 3.4 - Apply Blueprint

1. Clique em **Apply**
2. Aguarde ~3-5 minutos

**Processo:**
```
1. Creating database jsp-erp-db... ✅
2. Waiting for database to be available... ✅
3. Creating web service jsp-erp-backend... ✅
4. Running build command:
   - pip install... ✅
   - Running migrations (render_release.sh)... ✅
5. Starting service... ✅
6. Health check passed (/health)... ✅
7. Deploy live ✅
```

#### 3.5 - Obter URL

Após deploy:
- URL: `https://jsp-erp-backend.onrender.com`
- Status: 🟢 Live

---

## 🎨 Deploy Manual via Dashboard (Alternativo)

Se preferir configurar manualmente (sem render.yaml):

### 1. Criar Database

1. **New** → **PostgreSQL**
2. **Name:** `jsp-erp-db`
3. **Database:** `jsp_erp_production`
4. **User:** `jsp_user`
5. **Region:** Oregon
6. **Plan:** Starter ou Free
7. **Create Database**

### 2. Criar Web Service

1. **New** → **Web Service**
2. **Connect repository:** `JulianoSaroba123/jsp_erp`
3. **Name:** `jsp-erp-backend`
4. **Region:** Oregon
5. **Branch:** `master`
6. **Root Directory:** `backend`
7. **Runtime:** Python 3
8. **Build Command:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   chmod +x ../scripts/render_release.sh
   ../scripts/render_release.sh
   ```
9. **Start Command:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
   ```
10. **Plan:** Starter ou Free
11. **Advanced** → **Health Check Path:** `/health`

### 3. Configurar Environment Variables

Em **Environment**:

| Key | Value | Nota |
|-----|-------|------|
| `ENV` | `production` | Ambiente |
| `SECRET_KEY` | (clique "Generate") | Render gera automaticamente |
| `DATABASE_URL` | (selecione jsp-erp-db) | Auto-linked |
| `CORS_ALLOW_ORIGINS` | `https://seu-frontend.onrender.com` | ⚠️ Altere! |

4. **Create Web Service**

---

## 📋 Variáveis de Ambiente

### Obrigatórias

```bash
# Ambiente (local, development, production, test)
ENV=production

# JWT Secret (NUNCA usar valor padrão!)
SECRET_KEY=<render_gera_automaticamente>

# Database (auto-linked no Render)
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require

# CORS - domínios permitidos (CSV)
CORS_ALLOW_ORIGINS=https://seu-frontend.onrender.com,https://app.exemplo.com
```

### Opcionais

```bash
# Debug (default: false)
DEBUG=false

# Expiração JWT em minutos (default: 60)
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 🔑 Gerar SECRET_KEY Localmente

Se não usar Render auto-generate:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Output exemplo:**
```
XyZ1_AbC2-DeF3_GhI4-JkL5_MnO6-PqR7_StU8-VwX9_YzA0-BcD1_EfG2-HiJ3_KlM4
```

⚠️ **NUNCA** commitar no Git!

---

## � Migrations Automáticas (Alembic)

### Como Funciona

O script `scripts/render_release.sh` executa automaticamente durante o build:

```bash
#!/bin/bash
set -e  # Sai ao primeiro erro

# 1. Valida DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL not set!"
    exit 0  # Não falha build
fi

# 2. Navega para backend
cd "$(dirname "$0")/../backend"

# 3. Verifica Alembic instalado
if ! command -v alembic &> /dev/null; then
    echo "❌ ERROR: Alembic not found!"
    exit 1  # Falha build
fi

# 4. Mostra estado atual
alembic current

# 5. Roda migrations
alembic upgrade head

# 6. Mostra estado final
alembic current
```

### Logs de Migração (Render Build Logs)

Ao fazer deploy, você verá:

```
========================================
🚀 Render Release: Starting migrations
========================================
✅ DATABASE_URL found (postgresql://...)
📁 Working directory: /opt/render/project/src/backend
✅ Alembic found: alembic 1.13.0
📊 Current database state:
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
Current revision: abc123 (create users table)
🔄 Running migrations...
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456
✅ Migrations complete!
📊 Final database revision:
Current revision: def456 (add orders table)
========================================
✅ Render Release: Success
========================================
```

### Fallback: Migrations Manuais

Se migrations automáticas falharem:

```bash
# 1. Acessar Shell do Render
render shell -s jsp-erp-backend

# 2. Dentro do container
cd backend
alembic upgrade head

# 3. Verificar
alembic current
```

Ou via Render Dashboard:
1. Vá para `jsp-erp-backend` service
2. **Shell** tab
3. Execute: `cd backend && alembic upgrade head`

---

## ✅ Validação Pós-Deploy

### 1. Health Check Rápido

```bash
curl https://jsp-erp-backend.onrender.com/health
```

**Resposta esperada:**
```json
{
  "ok": true,
  "service": "jsp_erp",
  "env": "production",
  "database": "healthy"
}
```

✅ **Checklist:**
- `ok: true` → Serviço rodando
- `env: "production"` → Ambiente correto
- `database: "healthy"` → PostgreSQL conectado

❌ **Se `ok: false`:**
- Verifique logs: Dashboard > jsp-erp-backend > Logs
- Verifique DATABASE_URL: Dashboard > Environment
- Veja seção [Troubleshooting](#-troubleshooting)

---

### 2. Teste Manual de Autenticação

#### a) Registrar Usuário

```bash
curl -X POST https://jsp-erp-backend.onrender.com/auth/register \
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
  "created_at": "2026-02-23T12:00:00.000Z"
}
```

#### b) Login

```bash
curl -X POST https://jsp-erp-backend.onrender.com/auth/login \
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
  "token_type": "bearer"
}
```

#### c) Endpoint Autenticado

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl https://jsp-erp-backend.onrender.com/users/me \
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

## 🧪 Smoke Test Completo

**Recomendado:** Use o script de smoke test automatizado!

### Executar Smoke Test

```bash
cd scripts

# PowerShell (Windows)
$env:STAGING_BASE_URL="https://jsp-erp-backend.onrender.com"
python smoke_test_staging.py

# Bash (Linux/Mac)
STAGING_BASE_URL=https://jsp-erp-backend.onrender.com \
  python smoke_test_staging.py
```

### Output Esperado

```
🧪 SMOKE TEST - ERP JSP
========================================
Target: https://jsp-erp-backend.onrender.com
Time: 2026-02-23T12:34:56

TEST: Health Check
✅ Health check OK - env=production, db=healthy

TEST: User Registration
✅ User created: a1b2c3d4-e5f6-7890-abcd-ef1234567890

TEST: User Login
✅ Login successful - token obtained

TEST: Authenticated Endpoint (/users/me)
✅ Authentication OK - user: Smoke Test User

TEST: List Orders (Protected)
✅ Orders list OK - showing 0 of 0 total

📊 TEST SUMMARY
========================================
health               ✅ PASS
register             ✅ PASS
login                ✅ PASS
auth_endpoint        ✅ PASS
list_orders          ✅ PASS

✅ ALL TESTS PASSED (5/5)
Time: 2.34s

🎉 Staging is READY!
```

### Modo Verbose (Debugging)

```bash
# PowerShell
$env:VERBOSE="true"
$env:STAGING_BASE_URL="https://jsp-erp-backend.onrender.com"
python smoke_test_staging.py

# Bash
VERBOSE=true STAGING_BASE_URL=https://jsp-erp-backend.onrender.com \
  python smoke_test_staging.py
```

**Output com JSON completo:**
```json
{
  "ok": true,
  "service": "jsp_erp",
  "env": "production",
  "database": "healthy"
}
```

### Smoke Test no CI/CD

Adicione ao GitHub Actions (`.github/workflows/deploy.yml`):

```yaml
- name: Validate Deployment
  run: |
    STAGING_BASE_URL=https://jsp-erp-backend.onrender.com \
      python scripts/smoke_test_staging.py
  # Falha pipeline se smoke test falhar (exit code 1)
```

---

## 🚨 Troubleshooting

### ❌ Erro: "SECRET_KEY não configurado em produção"

**Mensagem:**
```
ValueError: SECRET_KEY must be configured in production
```

**Causa:** Variável `SECRET_KEY` não definida ou usando valor padrão.

**Solução:**

1. **Via Render Dashboard:**
   - Vá para `jsp-erp-backend` > **Environment**
   - Adicione `SECRET_KEY` e clique **Generate**
   - Save Changes (redeploy automático)

2. **Ou gere manualmente:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
   Cole no Environment Variables

---

### ❌ Erro: "CORS_ALLOW_ORIGINS é obrigatório em produção"

**Mensagem:**
```
ValueError: CORS_ALLOW_ORIGINS must be configured in production
```

**Causa:** `ENV=production` mas `CORS_ALLOW_ORIGINS` não configurado.

**Solução:**

1. Dashboard > jsp-erp-backend > **Environment**
2. Edite `CORS_ALLOW_ORIGINS`:
   ```
   https://seu-frontend.onrender.com,https://app.exemplo.com
   ```
3. Save Changes

**Nota:** Use domínios específicos. NUNCA `*` em produção!

---

### ❌ Health check retorna `"database": "unhealthy"`

**Resposta:**
```json
{
  "ok": false,
  "database": "unhealthy: connection refused"
}
```

**Diagnóstico:**

```bash
curl https://jsp-erp-backend.onrender.com/health | jq
```

**Causas possíveis:**

1. **DATABASE_URL incorreta**
   - Dashboard > Environment > DATABASE_URL
   - Deve começar com `postgresql://`
   - Deve terminar com `?sslmode=require` (Render adiciona automaticamente)

2. **PostgreSQL não provisionado**
   - Dashboard > jsp-erp-db
   - Status deve ser 🟢 Available
   - Se 🔴 Creating, aguarde ~2 minutos

3. **Migrations não aplicadas**
   ```bash
   render shell -s jsp-erp-backend
   cd backend
   alembic upgrade head
   ```

4. **Firewall/Network**
   - Render managed databases são auto-linked
   - Não precisa whitelist IPs

---

### ❌ Erro: SSL connection required

**Mensagem:**
```
psycopg.OperationalError: SSL connection required
```

**Causa:** DATABASE_URL sem SSL mode.

**Solução:**

Render adiciona automaticamente, mas se configurar manualmente:

```bash
# Errado
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Correto
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
```

---

### ❌ Migrations falham durante build

**Logs:**
```
❌ Migration failed: relation "users" does not exist
```

**Causa:** Primeiro deploy, tabelas não existem.

**Solução:**

1. **Criar migrations se não existem:**
   ```bash
   cd backend
   alembic revision --autogenerate -m "Initial tables"
   alembic upgrade head
   ```

2. **Ou rodar manualmente após deploy:**
   ```bash
   render shell -s jsp-erp-backend
   cd backend
   alembic upgrade head
   ```

---

### ⚠️ Free tier - serviço "spinningdown"

**Comportamento:**
- Render Free tier desliga serviço após 15min de inatividade
- Primeira request após spindown leva ~30-60s (cold start)

**Soluções:**

1. **Upgrade para Starter** ($7/mês)
   - Sempre ligado
   - Sem cold starts

2. **Ping periódico** (workaround gratuito)
   ```bash
   # Cron job externo (cron-job.org, EasyCron)
   curl https://jsp-erp-backend.onrender.com/health
   ```
   A cada 10 minutos evita spindown

---

### 🔍 Logs de Debug

**Via Dashboard:**
1. jsp-erp-backend > **Logs** tab
2. Filtros:
   - **Deploy Logs** → Build + migrations
   - **Runtime Logs** → Aplicação rodando

**Via CLI:**
```bash
# Install Render CLI
npm install -g render

# Login
render login

# Tail logs
render logs -s jsp-erp-backend --tail 100
```

**Logs de startup esperados:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
🚀 ERP JSP v1.0.0 iniciado
📍 Environment: production
✅ Database connection: OK
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
```

---

## 💰 Custos e Planos

### Opção 1: Starter Plan (Recomendado Produção)

**Web Service (jsp-erp-backend):**
- **Plano:** Starter
- **Custo:** **$7/mês**
- **Recursos:**
  - 512MB RAM
  - Always on (sem spindown)
  - Custom domains
  - SSL automático
  - Health checks

**PostgreSQL (jsp-erp-db):**
- **Plano:** Starter
- **Custo:** **$7/mês**
- **Recursos:**
  - 1GB storage
  - 97 connections
  - Backups diários (7 dias)
  - Point-in-time recovery

**Total: $14/mês (~R$ 70/mês)**

---

### Opção 2: Free Tier (Teste/Desenvolvimento)

⚠️ **Limitações importantes!**

**Web Service (Free):**
- **Custo:** **$0**
- **Limitações:**
  - Spins down após 15min inatividade
  - Cold start ~30-60s
  - 750 horas/mês (compartilhadas entre serviços)
  - Não recomendado para produção

**PostgreSQL (Free - Trial):**
- **Custo:** **$0 por 90 dias**
- **Após 90 dias:** Database é deletada ❌
- **Limitações:**
  - 256MB storage
  - 97 connections
  - Sem backups

**Total: $0 (mas limitado e expira em 90 dias)**

---

### Comparação de Planos

| Feature | Free | Starter ($14/mês) |
|---------|------|-------------------|
| Always on | ❌ | ✅ |
| Custom domains | ❌ | ✅ |
| Database backups | ❌ | ✅ 7 dias |
| Cold starts | 30-60s | Nenhum |
| Database persistence | 90 dias | Permanente |
| Produção | ❌ | ✅ |

---

### Reduzir Custos

**Opção A: Single Region**
- Deploy apenas em 1 região (Oregon = mais barato)
- Já configurado em `render.yaml` ✅

**Opção B: Combo com Railway**
- Web Service: Render Free (aceita spindown)
- Database: Railway ($5/mês com backups)
- Total: $5/mês (mas com cold starts)

**Opção C: Supabase Database**
- Web Service: Render Starter ($7/mês)
- Database: Supabase Free (500MB)
- Total: $7/mês
- Configure `DATABASE_URL` manualmente

---

## 📚 Documentação da API

Após deploy, acesse:

- **Swagger UI (interativo):** [https://jsp-erp-backend.onrender.com/docs](https://jsp-erp-backend.onrender.com/docs)
- **ReDoc (documentação):** [https://jsp-erp-backend.onrender.com/redoc](https://jsp-erp-backend.onrender.com/redoc)
- **OpenAPI JSON:** [https://jsp-erp-backend.onrender.com/openapi.json](https://jsp-erp-backend.onrender.com/openapi.json)

---

## 🔒 Checklist de Segurança

Antes de produção:

- [ ] `SECRET_KEY` gerada automaticamente (não padrão)
- [ ] `ENV=production` configurado
- [ ] `CORS_ALLOW_ORIGINS` com domínios específicos (NUNCA `*`)
- [ ] `DATABASE_URL` usando SSL (`?sslmode=require`)
- [ ] `DEBUG=false` (padrão)
- [ ] Credenciais apenas em Environment Variables
- [ ] Health check retornando `ok: true`
- [ ] Logs não vazando secrets
- [ ] Migrations aplicadas (`alembic current`)
- [ ] Smoke test passou (5/5)

---

## 📊 Monitoramento Contínuo

### Render Dashboard

1. **Metrics:** Dashboard > jsp-erp-backend > Metrics
   - CPU usage
   - Memory usage
   - Request rate
   - Response time

2. **Health Checks:** Auto-configurado em `/health`
   - Interval: 30s
   - Timeout: 10s
   - Unhealthy threshold: 3 falhas

3. **Alerts:** Dashboard > Settings > Notifications
   - Deploy failed
   - Health check failed
   - High error rate

### Logs

```bash
# Via CLI
render logs -s jsp-erp-backend --tail 100

# Via Dashboard
jsp-erp-backend > Logs > Runtime Logs
```

---

## 🎯 Próximos Passos

Após staging validado:

- [ ] Configurar monitoring externo (Sentry, DataDog)
- [ ] Implementar rate limiting customizado
- [ ] Configurar Redis para cache (opcional)
- [ ] Backups automáticos PostgreSQL (Starter plan já inclui)
- [ ] CI/CD com GitHub Actions
- [ ] Custom domain (`.com` próprio)
- [ ] Testes de carga (locust, k6)
- [ ] Plano de disaster recovery

---

## 🆘 Suporte

**Documentação Render:**
- [Render Docs](https://render.com/docs)
- [Blueprint Spec](https://render.com/docs/blueprint-spec)
- [PostgreSQL](https://render.com/docs/databases)

**Projeto:**
- **Issues:** [GitHub Issues](https://github.com/JulianoSaroba123/jsp_erp/issues)
- **Discussões:** [GitHub Discussions](https://github.com/JulianoSaroba123/jsp_erp/discussions)

**Render Support:**
- Free tier: Community support only
- Starter tier: Email support

---

**Última atualização:** 2026-02-23  
**Versão:** 2.0.0 (Render-optimized)  
**Autor:** Juliano Saroba

---

## 📝 Changelog

### v2.0.0 (2026-02-23) - Render Deployment
- ✨ Adicionado render.yaml Infrastructure as Code
- 🔄 Migrations automáticas via render_release.sh
- 🧪 Smoke test completo (scripts/smoke_test_staging.py)
- 📚 Documentação completa de deploy no Render
- 💰 Análise de custos (Free vs Starter)
- 🚨 Troubleshooting específico do Render

### v1.0.0 (2026-02-20) - Staging Preparation
- 📋 Variáveis de ambiente documentadas
- ✅ Health check implementado
- 🔐 Segurança: SECRET_KEY, CORS
- 📊 Validação pós-deploy manual

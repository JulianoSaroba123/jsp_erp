# 🚀 RUNBOOK: Deploy LIVE no Render

**Data:** 2026-02-23  
**Objetivo:** Colocar staging no ar e validar operação completa  
**Tempo estimado:** 15-20 minutos

---

## 📋 CHECKLIST PRÉ-DEPLOY

- [ ] Todos os testes passando localmente (236 tests)
- [ ] Coverage ≥ 85%
- [ ] Commit `3997d61` criado e verificado
- [ ] Git clean (sem uncommitted changes)
- [ ] render.yaml revisado (especialmente CORS_ALLOW_ORIGINS)

---

## 🔧 PASSO 0: Resolver Branch (CRÍTICO)

Seu repo está em `master`, mas a branch padrão é `main`. Escolha uma opção:

### Opção A: Push para master (render.yaml já aponta para master)

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'

# Verificar estado
git status
git log --oneline -1

# Push para master
git push origin master

# ✅ render.yaml já está configurado para branch: master
```

### Opção B: Merge para main (se preferir usar branch padrão)

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'

# Checkout para main
git checkout main

# Pull latest
git pull origin main

# Merge master
git merge master

# Push
git push origin main

# ⚠️ ALTERAR render.yaml:
# Mude: branch: master
# Para:  branch: main
```

**Recomendação:** Use **Opção A** (push master) para evitar alterar render.yaml.

---

## 🚀 PASSO 1: Deploy via Render Blueprint

### 1.1 - Acessar Dashboard

1. **URL:** https://dashboard.render.com
2. **Login:** Com GitHub
3. Clique: **New** → **Blueprint**

### 1.2 - Conectar Repositório

| Campo | Valor |
|-------|-------|
| **Repository** | `JulianoSaroba123/jsp_erp` |
| **Blueprint Name** | `jsp_erp` (ou deixe padrão) |
| **Blueprint file** | `render.yaml` ✅ (auto-detectado) |

### 1.3 - Revisar Serviços

**Web Service:**
- 🌐 **Name:** jsp-erp-backend
- **Type:** Web Service
- **Region:** Oregon
- **Plan:** Starter ($7/mês) ou Free (⚠️ cold starts)
- **Branch:** master ✅

**Database:**
- 🗄️ **Name:** jsp-erp-db
- **Type:** PostgreSQL 16
- **Region:** Oregon
- **Plan:** Starter ($7/mês) ou Free trial (90 dias)

### 1.4 - Apply Blueprint

1. Clique: **Apply**
2. **Aguarde:** ~3-5 minutos

**Fases do Deploy:**
```
1. Creating database jsp-erp-db...          [⏳ ~1-2 min]
2. Waiting for database availability...     [⏳ ~30s]
3. Creating web service jsp-erp-backend...  [⏳ ~30s]
4. Running build:
   - pip install -r requirements.txt        [⏳ ~1-2 min]
   - render_release.sh (migrations)         [⏳ ~10-30s]
5. Starting: uvicorn --workers 2            [⏳ ~10s]
6. Health check: GET /health                [⏳ ~5s]
7. ✅ Deploy live
```

---

## ☑️ PASSO 2: Confirmar Criação do Postgres

### Via Dashboard:

1. Dashboard → **jsp-erp-db**
2. **Status:** 🟢 **Available** (deve estar verde)
3. **Info tab:**
   - Database: `jsp_erp_production`
   - User: `jsp_user`
   - PostgreSQL: 16.x
   - Region: Oregon

### Conexão String:

**Internal Database URL** (visível em Info tab):
```
postgresql://jsp_user:***@***-postgres-***:5432/jsp_erp_production?sslmode=require
```

✅ **Checklist Database:**
- [ ] Status: Available (verde)
- [ ] PostgreSQL version: 16.x
- [ ] SSL mode: require (automático)
- [ ] Backups: Enabled (se Starter plan)

---

## 🔐 PASSO 3: Confirmar Environment Variables

### Via Dashboard:

1. **jsp-erp-backend** > **Environment** tab

**Variáveis Obrigatórias:**

| Key | Expected Value | Status |
|-----|---------------|---------|
| `ENV` | `production` | ✅ |
| `SECRET_KEY` | `[GENERATED]` (64+ chars) | ✅ |
| `DATABASE_URL` | `postgresql://...` (from jsp-erp-db) | ✅ |
| `CORS_ALLOW_ORIGINS` | `https://seu-frontend.onrender.com` | ⚠️ **EDIT** |

### ⚠️ AÇÃO OBRIGATÓRIA: Configurar CORS

1. Clique em **Edit** (lápis) ao lado de `CORS_ALLOW_ORIGINS`
2. **Mude de:**
   ```
   https://seu-frontend.onrender.com
   ```
3. **Para:** (escolha conforme seu caso)
   ```
   # Se não tem frontend ainda:
   https://jsp-erp-backend.onrender.com

   # Se tem frontend:
   https://seu-dominio-frontend.com

   # Múltiplos domínios:
   https://app.exemplo.com,https://admin.exemplo.com
   ```
4. **Save Changes** (triggers redeploy ~1-2 min)

✅ **Checklist Env Vars:**
- [ ] ENV = production
- [ ] SECRET_KEY gerada automaticamente (não é valor padrão)
- [ ] DATABASE_URL linkada automaticamente
- [ ] CORS_ALLOW_ORIGINS configurada com domínio real

---

## 🔄 PASSO 4: Confirmar Execução de Migrations

### Via Deploy Logs:

1. **jsp-erp-backend** > **Logs** tab
2. Filtro: **Deploy Logs**
3. **Buscar por:**

```
========================================
🚀 Render Release: Starting migrations
========================================
✅ DATABASE_URL found (postgresql://...)
📁 Working directory: /opt/render/project/src/backend
✅ Alembic found: alembic 1.13.0
📊 Current database state:
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
...
🔄 Running migrations...
INFO  [alembic.runtime.migration] Running upgrade ... -> ...
✅ Migrations complete!
📊 Final database revision:
...
========================================
✅ Render Release: Success
========================================
```

### Se NÃO aparecer migrations:

**Fallback Manual:**
```bash
render shell -s jsp-erp-backend
cd backend
alembic upgrade head
alembic current
```

**Ou via Dashboard:**
1. jsp-erp-backend > **Shell** tab
2. Execute:
   ```bash
   cd backend
   alembic upgrade head
   alembic current
   ```

✅ **Checklist Migrations:**
- [ ] Logs mostram "Render Release: Success"
- [ ] Alembic migrations executadas
- [ ] Tabelas criadas (users, orders, etc.)
- [ ] Sem erros de "relation does not exist"

---

## ▶️ PASSO 5: Confirmar Start do App

### Via Runtime Logs:

1. **jsp-erp-backend** > **Logs** tab
2. Filtro: **Runtime Logs**
3. **Buscar por:**

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
🚀 ERP JSP v1.0.0 iniciado
📍 Environment: production
🔒 CORS origins: ['https://seu-frontend.onrender.com']
🐛 Debug mode: False
✅ Database connection: OK
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
```

### ❌ Se aparecer erros:

**Erro:** `ModuleNotFoundError: No module named 'app'`
- **Causa:** rootDir incorreto em render.yaml
- **Fix:** Verificar que `rootDir: backend` está definido

**Erro:** `SECRET_KEY must be configured in production`
- **Causa:** SECRET_KEY não gerada
- **Fix:** Environment > SECRET_KEY > Generate

**Erro:** `CORS_ALLOW_ORIGINS must be configured`
- **Causa:** CORS vazio
- **Fix:** Environment > CORS_ALLOW_ORIGINS > editar

✅ **Checklist App Start:**
- [ ] "Application startup complete" visível
- [ ] "Environment: production"
- [ ] "Database connection: OK"
- [ ] Sem exceções/tracebacks
- [ ] Uvicorn rodando em porta 10000

---

## 🏥 PASSO 6: Validar /health

### 6.1 - Obter URL do Serviço

**Via Dashboard:**
- jsp-erp-backend > **Overview**
- **URL:** `https://jsp-erp-backend.onrender.com`

### 6.2 - Testar Health Endpoint

**PowerShell:**
```powershell
curl https://jsp-erp-backend.onrender.com/health
```

**CMD:**
```cmd
curl https://jsp-erp-backend.onrender.com/health
```

**Browser:**
- Abra: https://jsp-erp-backend.onrender.com/health

### 6.3 - Validar Resposta

**✅ Esperado (200 OK):**
```json
{
  "ok": true,
  "service": "jsp_erp",
  "env": "production",
  "database": "healthy"
}
```

**❌ Se `ok: false`:**
```json
{
  "ok": false,
  "database": "unhealthy: connection refused"
}
```
→ Veja seção [Troubleshooting](#-troubleshooting) abaixo

✅ **Checklist /health:**
- [ ] Status HTTP 200
- [ ] `ok: true`
- [ ] `env: "production"`
- [ ] `database: "healthy"`

---

## 📚 PASSO 7: Validar /docs (Swagger UI)

### 7.1 - Acessar Swagger

**URL:** https://jsp-erp-backend.onrender.com/docs

### 7.2 - Verificar Endpoints

**Esperado:**
- ✅ Swagger UI carrega
- ✅ Endpoints visíveis:
  - `GET /health`
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /users/me`
  - `GET /orders`
  - `POST /orders`
  - etc.

### 7.3 - Testar Autenticação (Opcional)

1. **Expand:** `POST /auth/register`
2. **Try it out**
3. **Body:**
   ```json
   {
     "email": "admin@exemplo.com",
     "password": "SenhaForte123!",
     "full_name": "Admin Render"
   }
   ```
4. **Execute**
5. **Esperado:** 201 Created

✅ **Checklist /docs:**
- [ ] Swagger UI carrega sem erros
- [ ] Endpoints listados corretamente
- [ ] POST /auth/register funciona (201)
- [ ] POST /auth/login retorna token

---

## 🧪 PASSO 8: Smoke Test E2E

### 8.1 - Comandos Exatos (PowerShell)

```powershell
# Navegue até a pasta scripts
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\scripts'

# Configure a URL do staging
$env:STAGING_BASE_URL = "https://jsp-erp-backend.onrender.com"

# Rode o smoke test
python smoke_test_staging.py

# Modo VERBOSE (debugging)
$env:VERBOSE = "true"
$env:STAGING_BASE_URL = "https://jsp-erp-backend.onrender.com"
python smoke_test_staging.py
```

### 8.2 - Comandos Exatos (CMD)

```cmd
REM Navegue até a pasta scripts
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\scripts"

REM Configure a URL do staging
set STAGING_BASE_URL=https://jsp-erp-backend.onrender.com

REM Rode o smoke test
python smoke_test_staging.py

REM Modo VERBOSE (debugging)
set VERBOSE=true
set STAGING_BASE_URL=https://jsp-erp-backend.onrender.com
python smoke_test_staging.py
```

### 8.3 - Output Esperado (SUCESSO)

```
🧪 SMOKE TEST - ERP JSP
========================================
Target: https://jsp-erp-backend.onrender.com
Time: 2026-02-23T15:30:00

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
Time: 2.45s

🎉 Staging is READY!
```

**Exit Code:** `0` (sucesso)

### 8.4 - Output de FALHA

```
🧪 SMOKE TEST - ERP JSP
========================================
Target: https://jsp-erp-backend.onrender.com
Time: 2026-02-23T15:30:00

TEST: Health Check
❌ Health check FAILED
   Status: 502
   Response: Bad Gateway

...

📊 TEST SUMMARY
========================================
health               ❌ FAIL
register             ⊘ SKIP (health failed)
login                ⊘ SKIP
auth_endpoint        ⊘ SKIP
list_orders          ⊘ SKIP

❌ SOME TESTS FAILED (0/5)

🚨 Staging NOT ready - check logs
```

**Exit Code:** `1` (falha)

✅ **Checklist Smoke Test:**
- [ ] Exit code: 0
- [ ] ALL TESTS PASSED (5/5)
- [ ] "Staging is READY!"

---

## 🚨 TROUBLESHOOTING

### ❌ Erro: 502 Bad Gateway ou 503 Service Unavailable

**Sintomas:**
```
❌ Health check FAILED
   Status: 502
   Response: Bad Gateway
```

**Causas possíveis:**

#### 1. Cold Start (Free Tier)

**Diagnóstico:**
- Service estava "sleeping" (inativo >15min)
- Primeira request leva 30-60s

**Fix:**
```powershell
# Aguarde 60s e tente novamente
Start-Sleep -Seconds 60
curl https://jsp-erp-backend.onrender.com/health
```

#### 2. Build Failed

**Diagnóstico:**
- Dashboard > jsp-erp-backend > **Events**
- Status: 🔴 "Deploy failed"

**Fix:**
1. Veja **Deploy Logs**
2. Procure por:
   - `ERROR: Could not find a version that satisfies...`
     → requirements.txt com dependência inexistente
   - `ModuleNotFoundError`
     → Import path incorreto
   - `alembic.util.exc.CommandError`
     → Migration failed

3. Corrija localmente, commit, push:
   ```powershell
   cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'
   # Fix o problema
   git add -A
   git commit -m "fix: Resolve build error"
   git push origin master
   ```

#### 3. Start Command Falhou

**Diagnóstico:**
- Runtime Logs mostram:
  ```
  ERROR: Error loading ASGI app
  ModuleNotFoundError: No module named 'app'
  ```

**Fix:**
- Verificar `rootDir: backend` em render.yaml
- Verificar `startCommand` usa caminho relativo correto:
  ```yaml
  startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
  ```

---

### ❌ Erro: 500 Internal Server Error em /health

**Sintomas:**
```
❌ Health check FAILED
   Status: 500
   Response: Internal Server Error
```

**Causas possíveis:**

#### 1. DATABASE_URL Incorreta

**Diagnóstico:**
- Runtime Logs:
  ```
  sqlalchemy.exc.OperationalError: could not connect to server
  ```

**Fix:**
1. Dashboard > jsp-erp-backend > **Environment**
2. Verificar `DATABASE_URL`:
   - Deve começar com `postgresql://`
   - Deve ter `?sslmode=require` no final
3. Se "from database" não linkado:
   - Delete `DATABASE_URL`
   - Re-add:
     - Key: `DATABASE_URL`
     - Value: `from database` > selecione `jsp-erp-db`

#### 2. SSL Mode Missing

**Diagnóstico:**
```
psycopg.OperationalError: SSL connection is required
```

**Fix:**
- Render adiciona automaticamente, mas verifique:
  ```
  postgresql://user:pass@host:5432/db?sslmode=require
  ```

#### 3. Alembic Migrations Não Executadas

**Diagnóstico:**
```
sqlalchemy.exc.ProgrammingError: relation "users" does not exist
```

**Fix:**
```bash
# Via Render Shell
render shell -s jsp-erp-backend
cd backend
alembic upgrade head
alembic current
```

---

### ❌ Erro: 401 Unauthorized ou 403 Forbidden

**Sintomas:**
```
TEST: User Login
❌ Login FAILED
   Status: 401
   Response: {"detail": "Invalid credentials"}
```

**Causas possíveis:**

#### 1. Usuário Não Existe

**Fix:**
- Smoke test cria usuário automaticamente
- Se testar manualmente:
  ```bash
  curl -X POST https://jsp-erp-backend.onrender.com/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"SenhaForte123!","full_name":"Test"}'
  ```

#### 2. Password Hash Incorreto

**Diagnóstico:**
- Database tem usuário mas login falha

**Fix:**
- Recrie usuário via `/auth/register`
- Verifique `security/password.py` usa bcrypt correto

#### 3. JWT Secret Incorreta

**Diagnóstico:**
```json
{"detail": "Could not validate credentials"}
```

**Fix:**
- Verificar `SECRET_KEY` configurada
- Environment > SECRET_KEY deve ter 64+ chars

---

### ❌ Erro: Timeout (Request Timeout)

**Sintomas:**
```
❌ Health check FAILED
   Error: Request timed out after 10s
```

**Causas possíveis:**

#### 1. Free Tier Cold Start

**Fix:**
- Aguarde até 60s para warm-up:
  ```powershell
  $env:STAGING_BASE_URL = "https://jsp-erp-backend.onrender.com"
  # Primeira request (pode timeout)
  curl $env:STAGING_BASE_URL/health
  # Aguarde
  Start-Sleep 60
  # Tente novamente
  curl $env:STAGING_BASE_URL/health
  ```

#### 2. Database Query Lenta

**Diagnóstico:**
- Runtime Logs:
  ```
  INFO: GET /health - took 15.3s
  ```

**Fix:**
- Verificar índices no banco
- Otimizar query do health check
- Upgrade database plan (mais recursos)

---

### ❌ Erro: Alembic Migration Errors

**Sintomas (Deploy Logs):**
```
❌ Migration failed
sqlalchemy.exc.ProgrammingError: column "deleted_at" already exists
```

**Causas possíveis:**

#### 1. Migration Duplicada

**Fix:**
```bash
render shell -s jsp-erp-backend
cd backend

# Ver histórico
alembic history

# Downgrade se necessário
alembic downgrade -1

# Re-upgrade
alembic upgrade head
```

#### 2. Inconsistência DB vs Migrations

**Fix (reset completo - ⚠️ PERDE DADOS):**
```bash
render shell -s jsp-erp-backend
cd backend

# Via psql (se disponível)
psql $DATABASE_URL -c "DROP TABLE alembic_version CASCADE;"

# Refazer migrations
alembic upgrade head
```

#### 3. Migration File Corrompido

**Fix:**
```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend'

# Deletar migration problemática
# Recriar
alembic revision --autogenerate -m "Fix migration"

# Commit e push
git add alembic/versions/
git commit -m "fix: Recreate migration"
git push origin master
```

---

## ✅ PASSO 9: Finalização (Quando Tudo OK)

### 9.1 - Criar Git Tag

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'

# Criar tag
git tag -a staging-live -m "Deploy: Staging live on Render

- URL: https://jsp-erp-backend.onrender.com
- Date: 2026-02-23
- Commit: 3997d61
- Tests: 236 passing
- Coverage: 85%
- Smoke Test: ✅ 5/5 passed
- Health: ✅ OK
- Database: ✅ Healthy
"

# Push tag
git push origin staging-live

# Verificar
git tag -l -n9 staging-live
```

### 9.2 - Atualizar Documentação com URL Final

```powershell
# Editar docs/DEPLOY_STAGING.md
# Adicionar seção no topo:
```

**Conteúdo a adicionar:**

```markdown
---

## 🟢 STAGING LIVE

**Status:** ✅ **LIVE and VALIDATED**

| Endpoint | URL | Status |
|----------|-----|--------|
| **Base URL** | https://jsp-erp-backend.onrender.com | 🟢 Live |
| **Health** | https://jsp-erp-backend.onrender.com/health | ✅ OK |
| **Swagger** | https://jsp-erp-backend.onrender.com/docs | ✅ OK |
| **ReDoc** | https://jsp-erp-backend.onrender.com/redoc | ✅ OK |

**Deploy Info:**
- **Data:** 2026-02-23
- **Commit:** `3997d61`
- **Git Tag:** `staging-live`
- **Tests:** 236 passing
- **Coverage:** 85%
- **Smoke Test:** ✅ 5/5 passed

**Database:**
- **Type:** PostgreSQL 16
- **Plan:** Starter ($7/mês)
- **Region:** Oregon
- **Backups:** Enabled (7 days)

**Validated:**
- ✅ Health check: OK
- ✅ Database connection: Healthy
- ✅ User registration: Working
- ✅ Authentication: Working
- ✅ Protected endpoints: Working
- ✅ Smoke test: All passed (5/5)

---
```

### 9.3 - Registrar Resultado em DEPLOY_STAGING.md

Adicionar no final do arquivo:

```markdown
---

## 📊 Deploy History

### 2026-02-23 - Initial Staging Deploy (staging-live)

**Status:** ✅ **SUCCESS**

**Environment:**
- Platform: Render.com
- Region: Oregon
- Plan: Starter ($14/mês)

**Services:**
- Web: https://jsp-erp-backend.onrender.com
- Database: jsp-erp-db (PostgreSQL 16)

**Validation:**
| Test | Result | Notes |
|------|--------|-------|
| Health Check | ✅ PASS | ok: true, db: healthy |
| User Registration | ✅ PASS | 201 Created |
| User Login | ✅ PASS | Token obtained |
| Authenticated Endpoint | ✅ PASS | /users/me working |
| Protected Resource | ✅ PASS | /orders accessible |
| **Smoke Test Overall** | ✅ **5/5 PASSED** | All E2E tests passed |

**Issues:** None

**Time to Deploy:** ~5 minutes

**Deployed by:** Juliano Saroba  
**Git Tag:** `staging-live`  
**Commit:** `3997d61`
```

### 9.4 - Commit Documentação Atualizada

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'

git add docs/DEPLOY_STAGING.md

git commit -m "docs: Update DEPLOY_STAGING.md with live staging info

- Add STAGING LIVE section with URLs
- Add deploy history entry
- Record smoke test results (5/5 passed)
- Document staging environment details
"

git push origin master
```

---

## 📝 CHECKLIST FINAL

**Deploy Completo:**
- [ ] Render Blueprint aplicado
- [ ] Database provisionada (jsp-erp-db)
- [ ] Env vars configuradas (ENV, SECRET_KEY, DATABASE_URL, CORS)
- [ ] Migrations executadas (render_release.sh)
- [ ] App iniciado (Uvicorn)
- [ ] /health retorna ok: true
- [ ] /docs (Swagger) acessível
- [ ] Smoke test passou (5/5)
- [ ] Git tag `staging-live` criada
- [ ] Documentação atualizada
- [ ] Commit final pushed

**URLs Validadas:**
- [ ] https://jsp-erp-backend.onrender.com (base)
- [ ] https://jsp-erp-backend.onrender.com/health
- [ ] https://jsp-erp-backend.onrender.com/docs
- [ ] https://jsp-erp-backend.onrender.com/redoc

**Testes E2E:**
- [ ] Health check: PASS
- [ ] User registration: PASS
- [ ] User login: PASS
- [ ] Authenticated endpoint: PASS
- [ ] Protected resource: PASS

---

## 🎉 SUCCESS!

Quando todos os checkboxes estiverem marcados:

**🟢 STAGING ESTÁ LIVE E VALIDADO!**

**Próximos passos:**
1. Configurar monitoring (Sentry/DataDog)
2. Configurar alertas (Render Notifications)
3. Testar com frontend (se disponível)
4. Planejar deploy de produção
5. Configurar custom domain (opcional)

---

**Última atualização:** 2026-02-23  
**Autor:** GitHub Copilot + Juliano Saroba

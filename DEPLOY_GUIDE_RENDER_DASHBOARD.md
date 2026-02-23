# 🚀 GUIA DE DEPLOY - RENDER DASHBOARD

**Instruções passo-a-passo para executar deploy via Render Blueprint**

---

## ⚡ PRÉ-REQUISITO: Git Push CONCLUÍDO ✅

Status: **COMPLETO**
- Branch: `master`
- Commits pushed: 9 commits
- Último commit: `b310d44`
- Repository: `JulianoSaroba123/jsp_erp`

---

## 📝 PASSO-A-PASSO NO RENDER DASHBOARD

### PASSO 1: Acessar Render

1. Abra seu navegador
2. Acesse: **https://dashboard.render.com**
3. Faça login com GitHub

---

### PASSO 2: Criar Blueprint

1. No dashboard, clique no botão **"New +"** (canto superior direito)
2. No menu dropdown, selecione: **"Blueprint"**

**Você verá:**
```
┌─────────────────────────────────────┐
│  New +  ▼                           │
├─────────────────────────────────────┤
│  Web Service                        │
│  Static Site                        │
│  Private Service                    │
│  Background Worker                  │
│  Cron Job                           │
│  Blueprint  ← CLIQUE AQUI           │
│  PostgreSQL                         │
│  Redis                              │
└─────────────────────────────────────┘
```

---

### PASSO 3: Conectar Repositório

**Tela: "Create a new Blueprint"**

1. **Section: Connect a repository**
   
   Localize e clique em: **`JulianoSaroba123/jsp_erp`**
   
   ⚠️ **SE NÃO APARECER:**
   - Clique em "Configure account" ou "Connect account"
   - Autorize Render a acessar seus repositórios no GitHub
   - Volte e procure novamente por `jsp_erp`

2. **Blueprint Name**
   
   Campo deve auto-preencher com: `jsp_erp`
   
   ✅ Deixe como está ou customize (ex: `jsp-erp-production`)

3. **Blueprint file**
   
   Render deve auto-detectar: `render.yaml`
   
   ✅ **VERIFICAR:** Deve aparecer "✓ Blueprint file detected"

**Tela deve mostrar:**
```
┌────────────────────────────────────────────┐
│ Connect a repository                       │
│ ○ JulianoSaroba123/jsp_erp     [Selected]  │
│                                            │
│ Blueprint Name                             │
│ [jsp_erp                              ]    │
│                                            │
│ Blueprint file detected                    │
│ ✓ render.yaml                              │
└────────────────────────────────────────────┘
```

4. Clique: **"Continue"** ou **"Next"**

---

### PASSO 4: Revisar Serviços

**Tela: "Review your Blueprint"**

Você verá 2 serviços listados:

#### 🌐 Web Service

```
┌──────────────────────────────────────────────┐
│ 🌐 WEB SERVICE                               │
├──────────────────────────────────────────────┤
│ Name:         jsp-erp-backend                │
│ Type:         Web Service                    │
│ Region:       Oregon                         │
│ Branch:       master                         │
│ Runtime:      Python 3                       │
│ Build:        pip install + render_release.sh│
│ Start:        uvicorn app.main:app ...       │
│ Plan:         Starter ($7/month)             │
│ Health Check: /health                        │
└──────────────────────────────────────────────┘
```

✅ **VERIFICAR:**
- Name: `jsp-erp-backend`
- Branch: `master` ✓
- Region: `Oregon` ✓
- Plan: `Starter` (ou `Free` se preferir)

#### 🗄️ Database

```
┌──────────────────────────────────────────────┐
│ 🗄️ POSTGRESQL                                │
├──────────────────────────────────────────────┤
│ Name:         jsp-erp-db                     │
│ Database:     jsp_erp_production             │
│ User:         jsp_user                       │
│ Region:       Oregon                         │
│ Plan:         Starter ($7/month)             │
│ Version:      PostgreSQL 16                  │
└──────────────────────────────────────────────┘
```

✅ **VERIFICAR:**
- Name: `jsp-erp-db`
- Database: `jsp_erp_production` ✓
- User: `jsp_user` ✓
- Region: `Oregon` ✓
- Plan: `Starter` (ou `Free` - trial 90 dias)

#### 💰 Custo Total

**Starter Plan:**
- Web Service: $7/month
- PostgreSQL: $7/month
- **Total: $14/month (~R$ 70/mês)**

**Free Plan (⚠️ Limitações):**
- Web Service: $0 (spins down após 15min)
- PostgreSQL: $0 (expira em 90 dias)
- **Total: $0**

---

### PASSO 5: Aplicar Blueprint

1. **Revise todos os detalhes acima**

2. **⚠️ ATENÇÃO:** Este passo criará recursos que podem gerar custos!

3. Clique no botão: **"Apply"** (azul, no rodapé)

**Confirmação:**
```
┌────────────────────────────────────────────┐
│ Apply Blueprint?                           │
│                                            │
│ This will create:                          │
│ • 1 Web Service ($7/mo or Free)            │
│ • 1 PostgreSQL Database ($7/mo or Free)    │
│                                            │
│ Total: ~$14/month                          │
│                                            │
│ [Cancel]              [Apply] ← CLIQUE     │
└────────────────────────────────────────────┘
```

4. Clique: **"Apply"** novamente para confirmar

---

### PASSO 6: Aguardar Deploy (~5-7 minutos)

**O Render iniciará o processo de deploy:**

#### Fase 1: Criando Database (1-2 minutos)

```
🗄️ jsp-erp-db
├─ Creating database...               [⏳]
├─ Provisioning storage...            [⏳]
├─ Starting PostgreSQL 16...          [⏳]
└─ Database available                 [✅] (1-2 min)
```

#### Fase 2: Criando Web Service (30s)

```
🌐 jsp-erp-backend
├─ Creating service...                [⏳]
├─ Configuring environment...         [⏳]
└─ Service created                    [✅] (30s)
```

#### Fase 3: Build (2-3 minutos)

```
🔨 Build
├─ Cloning repository...              [✅]
├─ Installing dependencies...         [⏳]
│  └─ pip install -r requirements.txt [⏳]
├─ Running render_release.sh...       [⏳]
│  ├─ Validating DATABASE_URL         [✅]
│  ├─ Running Alembic migrations      [⏳]
│  │  └─ alembic upgrade head         [✅]
│  └─ Migrations complete             [✅]
└─ Build complete                     [✅] (2-3 min)
```

#### Fase 4: Deploy (30s)

```
🚀 Deploy
├─ Starting Uvicorn...                [⏳]
├─ Running health check...            [⏳]
│  └─ GET /health                     [✅]
└─ Service live                       [✅] (30s)
```

#### Fase 5: Completo! ✅

```
✅ Deploy live

URL: https://jsp-erp-backend.onrender.com

Status: 🟢 Live
```

---

## 📊 MONITORAR DEPLOY

### Via Events Tab

1. No dashboard, clique em **`jsp-erp-backend`**
2. Aba: **"Events"**

Você verá:
```
┌────────────────────────────────────────────────┐
│ Recent Events                                  │
├────────────────────────────────────────────────┤
│ ✅ Deploy live (master@b310d44)                │
│    2 minutes ago                               │
│                                                │
│ ⏳ Deploy in progress                          │
│    5 minutes ago                               │
│                                                │
│ 🔨 Build started                               │
│    7 minutes ago                               │
└────────────────────────────────────────────────┘
```

### Via Logs Tab

1. Aba: **"Logs"**
2. Filtro: **"Deploy Logs"**

**Procure por:**
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
========================================
✅ Render Release: Success
========================================
```

3. Filtro: **"Runtime Logs"**

**Procure por:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
🚀 ERP JSP v1.0.0 iniciado
📍 Environment: production
🔒 CORS origins: ['https://seu-frontend.onrender.com']
✅ Database connection: OK
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

---

## ✅ CONFIRMAÇÕES OBRIGATÓRIAS

### 1. Web Service Status

**Local:** Dashboard → jsp-erp-backend → Overview

✅ **VERIFICAR:**
- Status: 🟢 **Live**
- URL: `https://jsp-erp-backend.onrender.com`
- Last Deploy: `< 10 minutos atrás`
- Health Check: ✅ Passing

### 2. Database Status

**Local:** Dashboard → jsp-erp-db → Info

✅ **VERIFICAR:**
- Status: 🟢 **Available**
- Database: `jsp_erp_production`
- User: `jsp_user`
- Version: `PostgreSQL 16.x`
- Connections: `0/97` (ou similar)

### 3. Environment Variables

**Local:** Dashboard → jsp-erp-backend → Environment

✅ **VERIFICAR EXISTÊNCIA:**

| Variable | Expected |
|----------|----------|
| `ENV` | `production` |
| `SECRET_KEY` | `[GENERATED]` (64+ chars, não vazio) |
| `DATABASE_URL` | `postgresql://...` (from jsp-erp-db) |
| `CORS_ALLOW_ORIGINS` | URL válida (não vazio) |

⚠️ **AÇÃO IMPORTANTE:** Editar `CORS_ALLOW_ORIGINS`

1. Clique no ícone de **lápis** ao lado de `CORS_ALLOW_ORIGINS`
2. **Altere de:**
   ```
   https://seu-frontend.onrender.com
   ```
3. **Para:** (escolha conforme seu caso)
   ```
   # Se ainda não tem frontend:
   https://jsp-erp-backend.onrender.com
   
   # Se tem frontend específico:
   https://seu-dominio-frontend.com
   ```
4. Clique: **"Save Changes"**
5. Aguarde redeploy (~1-2 min)

### 4. Migrations Aplicadas

**Local:** Dashboard → jsp-erp-backend → Shell

1. Abra **Shell** tab
2. Execute:
   ```bash
   cd backend
   alembic current
   ```

**Output esperado:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
abc123def456 (head)
```

✅ **VERIFICAR:** Mostra revisão atual (não "None")

---

## 🧪 VALIDAÇÃO AUTOMÁTICA

**Agora execute o script de validação que criei:**

### PowerShell (Recomendado)

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\scripts'

# Validação completa
.\validate_staging.ps1

# Modo verbose (detalhado)
.\validate_staging.ps1 -Verbose
```

**Output esperado:**
```
═════════════════════════════════════════
  🧪 VALIDAÇÃO DE STAGING - ERP JSP
═════════════════════════════════════════
ℹ️  Target: https://jsp-erp-backend.onrender.com
ℹ️  Time: 2026-02-23 15:30:00

TEST 1/4: Health Check
─────────────────────────────────────────
ℹ️  GET https://jsp-erp-backend.onrender.com/health
✅ Health check OK
ℹ️    Service: jsp_erp
ℹ️    Environment: production
ℹ️    Database: healthy

TEST 2/4: Swagger UI
─────────────────────────────────────────
ℹ️  GET https://jsp-erp-backend.onrender.com/docs
✅ Swagger UI accessible

TEST 3/4: ReDoc UI
─────────────────────────────────────────
ℹ️  GET https://jsp-erp-backend.onrender.com/redoc
✅ ReDoc accessible

TEST 4/4: Smoke Test E2E
─────────────────────────────────────────
ℹ️  Running: python smoke_test_staging.py
✅ Smoke test passed (5/5)

═════════════════════════════════════════
  📊 SUMMARY
═════════════════════════════════════════

health               ✅ PASS
docs                 ✅ PASS
redoc                ✅ PASS
smoke_test           ✅ PASS

─────────────────────────────────────────
✅ ALL TESTS PASSED (4/4)

🎉 STAGING IS READY!

Exit code: 0
```

---

## 🚨 SE DER ERRO

### Erro: 502 Bad Gateway

**Causa:** Cold start (Free tier) ou build falhou

**Fix:**
```powershell
# Aguarde 60 segundos
Start-Sleep 60

# Tente novamente
Invoke-WebRequest "https://jsp-erp-backend.onrender.com/health" -UseBasicParsing
```

**Se persistir:**
- Dashboard → jsp-erp-backend → Events
- Verifique se status é "Deploy failed"
- Se sim: veja Deploy Logs para erro específico

### Erro: 500 Internal Server Error

**Causa:** DATABASE_URL incorreta ou migrations não aplicadas

**Fix:**
```bash
# Via Render Shell
Dashboard → jsp-erp-backend → Shell

cd backend
alembic upgrade head
alembic current
```

### Erro: ValidationError em CORS

**Causa:** CORS_ALLOW_ORIGINS não configurado

**Fix:**
```
Dashboard → jsp-erp-backend → Environment
Edit CORS_ALLOW_ORIGINS
Value: https://jsp-erp-backend.onrender.com
Save Changes
```

### Smoke Test Falha

**Diagnóstico:**
```powershell
# Execute com verbose
.\validate_staging.ps1 -Verbose
```

**Consulte:**
- [RUNBOOK_DEPLOY_RENDER.md](RUNBOOK_DEPLOY_RENDER.md) - Seção Troubleshooting
- Dashboard → Logs → Runtime Logs

---

## ✅ CHECKLIST FINAL

Marque cada item após verificar:

**Deploy:**
- [ ] Render Blueprint aplicado
- [ ] jsp-erp-db: Status = Available 🟢
- [ ] jsp-erp-backend: Status = Live 🟢
- [ ] Deploy Logs: "Render Release: Success"
- [ ] Runtime Logs: "Application startup complete"

**Configuração:**
- [ ] ENV = production
- [ ] SECRET_KEY = gerada (64+ chars)
- [ ] DATABASE_URL = linkada automaticamente
- [ ] CORS_ALLOW_ORIGINS = configurada corretamente

**Validação:**
- [ ] Health check: OK (ok: true, database: healthy)
- [ ] Swagger UI: acessível em /docs
- [ ] ReDoc: acessível em /redoc
- [ ] Smoke test: 5/5 passed

**Finalizações:**
- [ ] validate_staging.ps1: ALL TESTS PASSED ✅
- [ ] Git tag criada: `staging-live`
- [ ] Documentação atualizada

---

## 🎯 PRÓXIMO PASSO

Após **TODOS os checkboxes marcados**, execute:

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'

# Criar tag
git tag -a staging-live -m "Deploy: Staging live on Render

URL: https://jsp-erp-backend.onrender.com
Date: $(Get-Date -Format 'yyyy-MM-dd')
Status: ✅ VALIDATED
Tests: 4/4 PASSED
"

# Push tag
git push origin staging-live

# Verificar
git tag -l -n9 staging-live
```

---

**Tempo total estimado:** 10-15 minutos

**Última atualização:** 2026-02-23  
**Autor:** GitHub Copilot

# ⚡ DEPLOY COMMANDS - CHEAT SHEET

**Consulta rápida para deploy no Render**

---

## 🔧 PRÉ-DEPLOY

```powershell
# ✅ Push para GitHub
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'
git status
git push origin master
```

**Render Dashboard:** https://dashboard.render.com  
**Action:** New → Blueprint → Connect `JulianoSaroba123/jsp_erp`

---

## 🧪 SMOKE TEST (PowerShell)

```powershell
# Navegue para scripts
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\scripts'

# Modo normal
$env:STAGING_BASE_URL = "https://jsp-erp-backend.onrender.com"
python smoke_test_staging.py

# Modo verbose (debugging)
$env:VERBOSE = "true"
$env:STAGING_BASE_URL = "https://jsp-erp-backend.onrender.com"
python smoke_test_staging.py
```

---

## 🧪 SMOKE TEST (CMD)

```cmd
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\scripts"

REM Modo normal
set STAGING_BASE_URL=https://jsp-erp-backend.onrender.com
python smoke_test_staging.py

REM Modo verbose
set VERBOSE=true
set STAGING_BASE_URL=https://jsp-erp-backend.onrender.com
python smoke_test_staging.py
```

---

## 🏥 QUICK HEALTH CHECK

```powershell
# PowerShell
curl https://jsp-erp-backend.onrender.com/health

# Esperado: {"ok": true, "service": "jsp_erp", "env": "production", "database": "healthy"}
```

---

## 🔍 TROUBLESHOOTING RÁPIDO

### 502/503 Error
```powershell
# Aguarde 60s (cold start)
Start-Sleep 60
curl https://jsp-erp-backend.onrender.com/health
```

### 500 Error (Database)
```bash
# Render Shell
render shell -s jsp-erp-backend
cd backend
alembic upgrade head
alembic current
```

### Verificar Logs
**Dashboard:** jsp-erp-backend → Logs → Deploy Logs / Runtime Logs

---

## ✅ PÓS-DEPLOY

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'

# Criar tag
git tag -a staging-live -m "Deploy: Staging live on Render - 2026-02-23"
git push origin staging-live

# Verificar
git tag -l -n9 staging-live
```

---

## 📋 VALIDATION CHECKLIST

- [ ] Health: https://jsp-erp-backend.onrender.com/health → `ok: true`
- [ ] Swagger: https://jsp-erp-backend.onrender.com/docs → loads OK
- [ ] Smoke test: `python smoke_test_staging.py` → 5/5 PASS
- [ ] Git tag: `staging-live` created and pushed

---

## 🚨 EMERGENCY ROLLBACK

```powershell
# Se deploy falhar completamente
# Dashboard → jsp-erp-backend → Manual Deploy → Previous commit
```

Ou via CLI:
```bash
render rollback -s jsp-erp-backend
```

---

## 📞 URLs IMPORTANTES

| Endpoint | URL |
|----------|-----|
| **Base** | https://jsp-erp-backend.onrender.com |
| **Health** | https://jsp-erp-backend.onrender.com/health |
| **Swagger** | https://jsp-erp-backend.onrender.com/docs |
| **ReDoc** | https://jsp-erp-backend.onrender.com/redoc |
| **Dashboard** | https://dashboard.render.com |

---

**Tempo estimado de deploy:** 5-7 minutos  
**Tempo smoke test:** ~3 segundos  
**Total:** ~10 minutos para deploy + validação completa

---

_Para detalhes completos, veja: [RUNBOOK_DEPLOY_RENDER.md](RUNBOOK_DEPLOY_RENDER.md)_

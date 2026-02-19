# 🧪 Guia Operacional de Testes - Backend ERP JSP

## Status Atual
- ✅ **38/38 testes passando** (100% green)
- ✅ **Coverage: 75%**
- ✅ **CI/CD: GitHub Actions integrado**

---

## 🚀 Quick Start (Desenvolvedor Local)

### 1. Pré-requisitos
```powershell
# PostgreSQL rodando localmente
# Python 3.11+ com venv ativo
# Estar no diretório backend/
```

### 2. Setup do Banco de Testes (apenas 1x)
```powershell
# Conectar ao PostgreSQL
psql -U postgres

# Criar database e usuário
CREATE DATABASE jsp_erp_test;
CREATE USER jsp_user WITH PASSWORD 'Admin123';
GRANT ALL PRIVILEGES ON DATABASE jsp_erp_test TO jsp_user;
\q
```

### 3. Configurar Credenciais (apenas 1x)
```powershell
# Copiar template
cp .env.test.example .env.test

# Editar .env.test com suas credenciais locais
# OBS: .env.test está no .gitignore (não será commitado)
```

### 4. Rodar Testes (comando oficial)
```powershell
# SEMPRE rodar deste diretório:
cd "C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"

# Opção 1: Script automático (recomendado)
.\scripts\test_local.ps1

# Opção 2: Pytest direto (se DATABASE_URL_TEST já estiver setado)
pytest -q --tb=short

# Opção 3: Com coverage HTML
pytest --cov --cov-report=html
# Abrir: htmlcov/index.html
```

---

## ❌ O Que NÃO Fazer

### 🚫 Erro #1: Rodar pytest fora do backend/
```powershell
# ❌ ERRADO (vai coletar arquivos do projeto Flask em C:\)
cd "C:\Users\julia\Desktop\ERP_JSP Training"
pytest

# ✅ CERTO
cd "C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"
pytest
```

### 🚫 Erro #2: Rodar sem DATABASE_URL_TEST
```powershell
# ❌ ERRADO (conftest.py vai explodir)
pytest

# ✅ CERTO (script seta automaticamente)
.\scripts\test_local.ps1
```

### 🚫 Erro #3: Alterar schema/status code sem atualizar testes
```powershell
# ❌ PERIGO: mudar OrderOut.total de float pra Decimal
# Vai quebrar 2 testes que esperam número JSON (não string)

# ✅ SAFE: manter float OU atualizar testes no mesmo commit
```

---

## 📊 Suíte de Testes (38 testes)

| Módulo | Testes | Cobertura | Crítico? |
|--------|--------|-----------|----------|
| `test_auth_login.py` | 8 | Login, registro, JWT | ⚠️ CRÍTICO |
| `test_patch_orders.py` | 7 | PATCH /orders + sync financeiro | ⚠️ CRÍTICO |
| `test_orders_get_post_delete.py` | 8 | CRUD orders + multi-tenant | ✅ Alta |
| `test_financial_idempotency.py` | 6 | Idempotência, UNIQUE constraint | ✅ Alta |
| `test_reports_smoke.py` | 7 | DRE, cashflow, aging, top | ✅ Média |
| `test_health.py` | 2 | Health checks | ✅ Baixa |

### Testes Críticos (Não Podem Regredir)
1. **PATCH /orders** (7/7 green) - 5 regras de sincronização financeira
2. **Idempotência** - UNIQUE constraint em `financial_entry.order_id`
3. **Multi-tenant** - User vê só seus dados, admin vê tudo
4. **HTTP Status** - 409 para conflitos de negócio (não 400/403)

---

## 🔧 Troubleshooting

### Problema: "transaction already deassociated from connection"
**Sintoma:** Warning no teardown do conftest.py  
**Causa:** Rollback duplo após teste já ter finalizado transaction  
**Fix:** Aplicado em `conftest.py` linha 117 (checar `transaction.is_active`)

### Problema: "No module named flask"
**Sintoma:** Pytest coleta arquivos errados  
**Causa:** Rodou pytest fora do backend/  
**Fix:** `cd backend; .\scripts\test_local.ps1`

### Problema: "Database jsp_erp_test does not exist"
**Sintoma:** FATAL no setup dos testes  
**Causa:** DB não foi criado  
**Fix:** Ver seção "Setup do Banco de Testes"

### Problema: Testes passam local, falham no CI
**Sintoma:** GitHub Actions red, local green  
**Possíveis causas:**
1. Alembic migrations não rodaram (`alembic upgrade head`)
2. DATABASE_URL_TEST incorreto no CI
3. Postgres version mismatch (CI usa Postgres 15)

---

## 🏗️ Estrutura de Isolamento Transacional

```python
# Estratégia: Transaction + ROLLBACK (sem SAVEPOINT, sem TRUNCATE)
engine_test (session scope)
  └─ db_connection (function scope) 
      └─ db_session (function scope)
          └─ client (function scope, override get_db)

# Cada teste roda em transaction própria
# Teardown: connection.rollback() → cleanup automático
# commit() é sobrescrito pra flush() → visibilidade entre layers
```

**Vantagens:**
- ✅ 100% isolado (zero poluição entre testes)
- ✅ Rápido (sem DROP TABLE / CREATE TABLE)
- ✅ Visibilidade correta (API + teste veem mesma sessão)

---

## 📝 Checklist Pre-Commit

Antes de dar push, sempre rodar:

```powershell
# 1. Testes passando
.\scripts\test_local.ps1
# Esperado: 38 passed

# 2. Linter (se houver)
# flake8 app tests

# 3. Coverage >= 75%
pytest --cov
# Verificar: TOTAL >= 75%

# 4. Migrations aplicadas
alembic upgrade head

# 5. .env.test não commitado
git status | Select-String ".env.test"
# Esperado: vazio (ou só .env.test.example)
```

---

## 🚢 CI/CD (GitHub Actions)

**Workflow:** `.github/workflows/tests.yml`

**Secrets necessários:**
- `DATABASE_URL_TEST` - Setado automaticamente pelo service postgres
- `SECRET_KEY` - Setado no env do workflow

**Pipeline:**
1. Setup Postgres 15 + healthcheck
2. CREATE DATABASE jsp_erp_test
3. Alembic migrations (`alembic upgrade head`)
4. Pytest + Coverage
5. Upload coverage HTML (artifact, 7 dias)

**Como ver coverage do CI:**
1. Actions → workflow run → Artifacts
2. Download `coverage-report`
3. Abrir `index.html`

---

## 📞 Suporte

**Dúvidas sobre testes:**
- Ver contexto: `docs/PRONTIDAO_ETAPA_1.md`
- Ver diagnóstico: `docs/DIAGNOSTICO_TECNICO_POSTGRESQL.md`

**Regression em PATCH /orders:**
- Ver implementação: `docs/ETAPA_1_CONCLUSAO.md`
- Testar manual: `docs/COMANDOS_RETESTE.md`

**Mudança de schema/contrato:**
- SEMPRE atualizar testes no mesmo PR
- SEMPRE manter alias por 1 release (compatibilidade)
- NUNCA quebrar PATCH /orders sem RFC

# RBAC Migration 005 - Validation Guide

## ✅ Validação Local (Passo a Passo)

### 1. Aplicar Migration 005 (Idempotente)

```powershell
cd backend
alembic upgrade head
```

**Output esperado:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 004_add_rbac -> 005_rbac_idempotent, RBAC: Create tables if missing (idempotent fix)
```

**Verificar estado:**
```powershell
alembic current
```

**Deve mostrar:**
```
005_rbac_idempotent (head)
```

---

### 2. Validar Estrutura com Testes de Schema

```powershell
pytest tests/test_rbac_schema.py -v
```

**Testes executados (9 total):**

✅ `test_rbac_tables_exist` - Valida que 4 tabelas existem  
✅ `test_roles_table_structure` - Valida colunas da tabela roles  
✅ `test_permissions_table_structure` - Valida colunas da tabela permissions  
✅ `test_permissions_unique_constraint` - Valida UNIQUE(resource, action)  
✅ `test_user_roles_foreign_keys` - Valida FKs em user_roles  
✅ `test_role_permissions_foreign_keys` - Valida FKs em role_permissions  
✅ `test_rbac_indexes_exist` - Valida índices de performance  
✅ `test_cannot_create_duplicate_permissions` - Testa integridade  
✅ `test_cascade_delete_role_removes_associations` - Testa CASCADE  

**Esperado:** `9 passed` ✅

---

### 3. Popular Dados (Seeds)

```powershell
python -m app.scripts.seed_rbac
```

**Output esperado:**
```
============================================================
  SEED RBAC - Roles e Permissions
============================================================

[1/3] Criando permissions...
   + Criada permission: orders:read
   + Criada permission: orders:create
   ...
   ✓ Total: 14 permissions

[2/3] Criando roles...
   + Criada role: admin
   + Criada role: user
   + Criada role: finance
   ✓ Total: 3 roles

[3/3] Atribuindo roles aos usuários existentes...
   + Atribuída role 'admin' ao usuário admin@jsp.com
   ...
   ✓ Usuários atualizados

============================================================
  ✓ SEED COMPLETO
============================================================
```

---

### 4. Validar Funcionalidade com Testes RBAC

```powershell
pytest tests/test_rbac.py -v
```

**Testes executados (4 total):**

✅ `test_user_has_permission_method` - Valida lógica de permissões  
✅ `test_permission_full_name` - Valida property full_name  
✅ `test_role_permissions_association` - Valida N:N roles-permissions  
✅ `test_user_roles_association` - Valida N:N users-roles  

**Esperado:** `4 passed` ✅

---

## 🔄 Idempotência (Pode rodar múltiplas vezes)

### Testar Idempotência da Migration

```powershell
# Rodar upgrade múltiplas vezes (deve ser seguro)
cd backend
alembic upgrade head
alembic upgrade head
alembic upgrade head
```

**Não deve haver erros.** As tabelas já existem, `IF NOT EXISTS` previne duplicatas.

### Testar Idempotência dos Seeds

```powershell
# Rodar seeds múltiplas vezes
python -m app.scripts.seed_rbac
python -m app.scripts.seed_rbac
```

**Output esperado:**
```
[1/3] Criando permissions...
   ✓ Permission já existe: orders:read
   ✓ Permission já existe: orders:create
   ...
```

---

## 🚀 Setup CI/CD (GitHub Actions / Render / etc)

### Comandos para CI Pipeline

```yaml
# .github/workflows/deploy.yml ou Render Build Commands

steps:
  # 1. Instalar dependências
  - pip install -r backend/requirements.txt
  
  # 2. Aplicar migrations (idempotente)
  - cd backend && alembic upgrade head
  
  # 3. Validar estrutura (OBRIGATÓRIO em CI)
  - pytest tests/test_rbac_schema.py -v --tb=short
  
  # 4. Popular seeds (idempotente)
  - python -m app.scripts.seed_rbac
  
  # 5. Rodar testes funcionais
  - pytest tests/test_rbac.py -v
```

**Policy CI:** Se algum teste de schema falhar, CI deve falhar ❌

---

## ❌ Troubleshooting

### Problema: "relation 'core.roles' does not exist"

**Causa:** Migration 005 não foi aplicada.

**Solução:**
```powershell
cd backend
alembic current  # Ver estado atual
alembic upgrade head  # Aplicar migrations
pytest tests/test_rbac_schema.py -v  # Validar
```

---

### Problema: Testes de schema falham

**Causa:** Migration 005 não criou estrutura correta ou banco está inconsistente.

**Solução (Ambiente DEV):**
```powershell
# 1. Downgrade para 004
cd backend
alembic downgrade 004_add_rbac

# 2. Re-aplicar 005
alembic upgrade head

# 3. Validar
pytest tests/test_rbac_schema.py -v
```

**Solução (Banco limpo - DESTRUIR DADOS):**
```powershell
# ⚠️ CUIDADO: destroi todo schema RBAC
cd backend
alembic downgrade 003

# Recriar do zero
alembic upgrade head
pytest tests/test_rbac_schema.py -v
python -m app.scripts.seed_rbac
```

---

### Problema: "IntegrityError: duplicate key value violates unique constraint"

**Causa:** Tentando rodar seeds com dados já existentes sem verificação idempotente.

**Solução:** Seeds já são idempotentes (verificam se existe antes de criar). Se erro persiste:
```powershell
# Limpar tabelas RBAC manualmente
python backend/clean_rbac_tables.py

# Re-seed
cd backend
python -m app.scripts.seed_rbac
```

---

## 📊 Status Final Esperado

Após seguir todos os passos:

✅ Migration 005 aplicada (`alembic current` → `005_rbac_idempotent`)  
✅ 9 testes de schema passando  
✅ 4 tabelas RBAC existem (roles, permissions, user_roles, role_permissions)  
✅ 14 permissions populadas  
✅ 3 roles populadas  
✅ 4+ usuários com roles atribuídas  
✅ 4 testes funcionais RBAC passando  
✅ Endpoint DELETE /orders protegido com `orders:delete`  

---

## 🎯 Diferenças em Relação ao Workaround Manual

### Antes (Migration 004 + Script Manual)

❌ Migration 004 não criava tabelas (bug transacional)  
❌ Necessário rodar `create_rbac_tables_manual.py` em cada ambiente  
❌ CI/CD precisava de step extra não-reprodutível  
❌ Sem validação automática de estrutura  

### Agora (Migration 005 Idempotente)

✅ Migration 005 cria tabelas com `IF NOT EXISTS`  
✅ Totalmente reprodutível via `alembic upgrade head`  
✅ CI/CD usa apenas migrations padrão  
✅ Testes de schema validam estrutura automaticamente  
✅ Idempotente → seguro rodar múltiplas vezes  

---

## 📝 Checklist de Deploy

- [ ] `alembic upgrade head` executado com sucesso
- [ ] `alembic current` mostra `005_rbac_idempotent (head)`
- [ ] `pytest tests/test_rbac_schema.py -v` → 9 passed
- [ ] `python -m app.scripts.seed_rbac` executado
- [ ] `pytest tests/test_rbac.py -v` → 4 passed
- [ ] Endpoint DELETE /orders retorna 403 para users sem permissão
- [ ] Endpoint DELETE /orders funciona para admins com permissão

**Se todos checkmarks OK:** RBAC está 100% funcional ✅

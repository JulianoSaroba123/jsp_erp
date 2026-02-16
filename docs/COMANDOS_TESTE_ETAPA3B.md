# COMANDOS DE TESTE - ETAPA 3B (Alembic Migrations)

**Testes Executáveis Copy/Paste**

---

## 📋 Pré-requisitos

1. PostgreSQL rodando
2. Arquivo `backend/.env` configurado com `DATABASE_URL`
3. Dependências instaladas: `pip install -r backend/requirements.txt`

---

## 🧪 TESTE 1: Verificar Instalação do Alembic

### Windows (PowerShell)

```powershell
cd backend
python -m alembic --version
```

### Linux/macOS (Bash)

```bash
cd backend
python -m alembic --version
```

### ✅ Resultado Esperado

```
alembic 1.x.x
```

---

## 🧪 TESTE 2: Verificar Configuração (Current - Banco Vazio)

**Objetivo:** Ver status atual do banco (deve dar erro se não inicializado).

### Windows (PowerShell)

```powershell
cd backend
python -m alembic current 2>&1
```

### Linux/macOS (Bash)

```bash
cd backend
python -m alembic current 2>&1
```

### ✅ Resultado Esperado (Banco Vazio)

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedTable) relation "core.alembic_version" does not exist
```

**Isso é normal!** Significa que o Alembic ainda não foi inicializado.

---

## 🧪 TESTE 3: Aplicar Migration Baseline (Banco Vazio)

**Objetivo:** Criar schema `core` + tabelas pela primeira vez.

### Windows (PowerShell)

```powershell
# Via script utilitário
.\scripts\migrate.ps1 upgrade

# OU via Alembic direto
cd backend
python -m alembic upgrade head
```

### Linux/macOS (Bash)

```bash
# Via script utilitário
./scripts/migrate.sh upgrade

# OU via Alembic direto
cd backend
python -m alembic upgrade head
```

### ✅ Resultado Esperado

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_baseline, baseline_schema_core_users_orders_financial
✅ Migration aplicada com sucesso!
```

---

## 🧪 TESTE 4: Verificar Versão Atual (Após Upgrade)

### Windows (PowerShell)

```powershell
.\scripts\migrate.ps1 current

# OU
cd backend
python -m alembic current
```

### Linux/macOS (Bash)

```bash
./scripts/migrate.sh current

# OU
cd backend
python -m alembic current
```

### ✅ Resultado Esperado

```
001_baseline (head)
```

---

## 🧪 TESTE 5: Verificar Tabelas no PostgreSQL

**Objetivo:** Confirmar que as tabelas foram criadas.

### Conectar ao PostgreSQL

```sql
-- Windows (via psql ou pgAdmin)
psql -U postgres -d jsp_erp

-- Linux/macOS
psql -U postgres -d jsp_erp
```

### Comandos SQL

```sql
-- Ver schemas
\dn

-- Resultado esperado:
--   Name  | Owner
--  -------+-------
--   core  | ...
--   public| ...

-- Ver tabelas no schema core
\dt core.*

-- Resultado esperado:
--          List of tables
--  Schema |       Name            | Type  | Owner
-- --------+-----------------------+-------+-------
--  core   | alembic_version       | table | ...
--  core   | users                 | table | ...
--  core   | orders                | table | ...
--  core   | financial_entries     | table | ...

-- Ver versão do Alembic
SELECT * FROM core.alembic_version;

-- Resultado esperado:
--  version_num
-- -------------
--  001_baseline

-- Ver estrutura de uma tabela
\d core.users

-- Resultado esperado:
--                            Table "core.users"
--     Column     |            Type             | Collation | Nullable | Default
-- ---------------+-----------------------------+-----------+----------+---------
--  id            | uuid                        |           | not null | gen_random_uuid()
--  name          | character varying(150)      |           | not null |
--  email         | character varying(255)      |           | not null |
--  password_hash | character varying           |           | not null |
--  role          | character varying(50)       |           | not null |
--  is_active     | boolean                     |           |          | true
--  created_at    | timestamp without time zone |           |          | now()
-- Indexes:
--     "users_pkey" PRIMARY KEY, btree (id)
--     "users_email_key" UNIQUE CONSTRAINT, btree (email)
--     "ix_core_users_email" UNIQUE, btree (email)
-- Check constraints:
--     "check_user_role" CHECK (role::text = ANY (ARRAY['admin'::character varying, 'user'::character varying, 'viewer'::character varying]::text[]))

-- Ver índices de financial_entries
\d core.financial_entries

-- Verificar índices (deve incluir):
--  - idx_financial_entries_user_occurred
--  - idx_financial_entries_status
--  - idx_financial_entries_order (partial index)
--  - idx_financial_entries_kind
```

### Sair do psql

```sql
\q
```

---

## 🧪 TESTE 6: Ver Histórico de Migrations

### Windows (PowerShell)

```powershell
.\scripts\migrate.ps1 history

# OU
cd backend
python -m alembic history --verbose
```

### Linux/macOS (Bash)

```bash
./scripts/migrate.sh history

# OU
cd backend
python -m alembic history --verbose
```

### ✅ Resultado Esperado

```
Rev: 001_baseline (head)
Parent: <base>
Path: /.../backend/alembic/versions/001_baseline.py

    baseline_schema_core_users_orders_financial
    
    Revision ID: 001_baseline
    Revises: 
    Create Date: 2026-02-16 00:00:00.000000
```

---

## 🧪 TESTE 7: Criar Nova Migration (Autogenerate)

**Objetivo:** Simular adição de um campo e verificar autogenerate.

### 1. Editar Model (Simulação)

**Windows (PowerShell):**
```powershell
# Adicionar comentário ao model User para testar autogenerate
# (Alembic não detectará apenas comentário, então adicionar coluna de teste)
```

**Adicionar ao `backend/app/models/user.py`:**
```python
# Após a coluna 'created_at', adicionar:
test_field = Column(String(50), nullable=True, comment="Campo de teste")
```

### 2. Gerar Migration

**Windows (PowerShell):**
```powershell
cd backend
python -m alembic revision --autogenerate -m "add_test_field_to_users"
```

**Linux/macOS (Bash):**
```bash
cd backend
python -m alembic revision --autogenerate -m "add_test_field_to_users"
```

### ✅ Resultado Esperado

```
INFO  [alembic.autogenerate.compare] Detected added column 'users.test_field'
  Generating /.../versions/20260216_1430_002_add_test_field_to_users.py ... done
```

### 3. Revisar Migration Gerada

**Windows (PowerShell):**
```powershell
# Ver arquivo gerado
ls backend\alembic\versions\

# Abrir no editor
notepad backend\alembic\versions\20260216_*_add_test_field_to_users.py
```

**Linux/macOS (Bash):**
```bash
# Ver arquivo gerado
ls backend/alembic/versions/

# Abrir no editor
cat backend/alembic/versions/20260216_*_add_test_field_to_users.py
```

### ✅ Verificar Conteúdo

Deve conter:
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('test_field', sa.String(length=50), nullable=True, comment='Campo de teste'), schema='core')

def downgrade() -> None:
    op.drop_column('users', 'test_field', schema='core')
```

### 4. Aplicar Migration

**Windows (PowerShell):**
```powershell
.\scripts\migrate.ps1 upgrade
```

**Linux/macOS (Bash):**
```bash
./scripts/migrate.sh upgrade
```

### ✅ Resultado Esperado

```
INFO  [alembic.runtime.migration] Running upgrade 001_baseline -> 002, add_test_field_to_users
✅ Migration aplicada com sucesso!
```

### 5. Verificar no Banco

```sql
-- Conectar ao PostgreSQL
psql -U postgres -d jsp_erp

-- Ver estrutura atualizada
\d core.users

-- Resultado esperado (nova coluna):
--  test_field | character varying(50) | | |

-- Ver versão
SELECT * FROM core.alembic_version;

-- Resultado esperado:
--  version_num
-- -------------
--  002  (ou revision ID da nova migration)

\q
```

---

## 🧪 TESTE 8: Reverter Migration (Downgrade)

**Objetivo:** Testar rollback (remover campo `test_field`).

### Windows (PowerShell)

```powershell
.\scripts\migrate.ps1 downgrade -1

# O script pedirá confirmação:
# ⚠️  ATENÇÃO: Downgrade pode remover dados!
# Confirma downgrade para '-1'? (s/N)
# Digite: s
```

### Linux/macOS (Bash)

```bash
./scripts/migrate.sh downgrade -1

# O script pedirá confirmação:
# ⚠️  ATENÇÃO: Downgrade pode remover dados!
# Confirma downgrade para '-1'? (s/N)
# Digite: s
```

### ✅ Resultado Esperado

```
INFO  [alembic.runtime.migration] Running downgrade 002 -> 001_baseline, add_test_field_to_users
✅ Downgrade executado com sucesso
```

### Verificar no Banco

```sql
psql -U postgres -d jsp_erp

-- Ver estrutura
\d core.users

-- Resultado esperado:
-- Coluna 'test_field' não existe mais

-- Ver versão
SELECT * FROM core.alembic_version;

-- Resultado esperado:
--  version_num
-- -------------
--  001_baseline

\q
```

---

## 🧪 TESTE 9: Stamp (Banco Existente)

**Objetivo:** Simular adoção do Alembic em banco criado via scripts SQL.

**⚠️ IMPORTANTE:** Este teste só é relevante se você tem um banco criado pelos scripts SQL antigos.

### Cenário: Banco Já Existe (Via Scripts SQL)

Se você já executou os scripts `database/*.sql` manualmente, o banco tem as tabelas mas **não tem** `core.alembic_version`.

### 1. Verificar Estado Atual

```sql
psql -U postgres -d jsp_erp

-- Ver tabelas
\dt core.*

-- Resultado esperado (se criadas via SQL):
--  core.users
--  core.orders
--  core.financial_entries
--  (MAS NÃO core.alembic_version)

\q
```

### 2. Marcar como Aplicada (Stamp)

**Windows (PowerShell):**
```powershell
.\scripts\migrate.ps1 stamp head

# OU
cd backend
python -m alembic stamp 001_baseline
```

**Linux/macOS (Bash):**
```bash
./scripts/migrate.sh stamp head

# OU
cd backend
python -m alembic stamp 001_baseline
```

### ✅ Resultado Esperado

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Stamping revision table with 001_baseline
✅ Database marcado como versão: head
```

### 3. Verificar no Banco

```sql
psql -U postgres -d jsp_erp

-- Ver tabela de versão (agora existe)
SELECT * FROM core.alembic_version;

-- Resultado esperado:
--  version_num
-- -------------
--  001_baseline

\q
```

### 4. Verificar Current

```powershell
# Windows
.\scripts\migrate.ps1 current

# Linux/macOS
./scripts/migrate.sh current
```

### ✅ Resultado Esperado

```
001_baseline (head)
```

**Pronto!** Agora o Alembic reconhece o banco como na versão baseline, e futuras migrations serão aplicadas normalmente.

---

## 🧪 TESTE 10: Validação Final (Integração com App)

**Objetivo:** Confirmar que o app FastAPI funciona com o schema criado via Alembic.

### 1. Iniciar App

**Windows (PowerShell):**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

**Linux/macOS (Bash):**
```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

### 2. Testar Endpoint de Health

```powershell
# Windows
curl.exe http://localhost:8000/health

# Linux/macOS
curl http://localhost:8000/health
```

### ✅ Resultado Esperado

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "..."
}
```

### 3. Testar Criação de Usuário (Via Alembic Schema)

```powershell
# Criar usuário de teste
curl.exe -X POST "http://localhost:8000/auth/register" `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Teste Alembic",
    "email": "teste.alembic@example.com",
    "password": "senha123",
    "role": "user"
  }'
```

### ✅ Resultado Esperado

```json
{
  "id": "...",
  "name": "Teste Alembic",
  "email": "teste.alembic@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "..."
}
```

### 4. Verificar no Banco

```sql
psql -U postgres -d jsp_erp

-- Ver usuário criado
SELECT id, name, email, role FROM core.users WHERE email = 'teste.alembic@example.com';

-- Resultado esperado:
--                  id                  |     name      |           email               | role
-- -------------------------------------+---------------+-------------------------------+------
--  <UUID>                              | Teste Alembic | teste.alembic@example.com     | user

\q
```

---

## 🧹 LIMPEZA (Opcional)

Se quiser resetar o banco para testes futuros:

### Opção 1: Downgrade Completo (Via Alembic)

```powershell
# Windows
.\scripts\migrate.ps1 downgrade base

# Linux/macOS
./scripts/migrate.sh downgrade base
```

**Isso remove TODAS as tabelas e o schema core.**

### Opção 2: Drop Manual (SQL)

```sql
psql -U postgres -d jsp_erp

-- Remover tudo do schema core
DROP SCHEMA core CASCADE;

-- Recriar schema vazio
CREATE SCHEMA core;

\q
```

### Recriar do Zero

Após limpeza:

```powershell
# Windows
.\scripts\migrate.ps1 upgrade

# Linux/macOS
./scripts/migrate.sh upgrade
```

---

## 📊 Checklist de Validação

Após executar todos os testes, confirme:

- [ ] `alembic --version` funciona
- [ ] `alembic current` mostra versão correta
- [ ] `alembic upgrade head` cria schema core + tabelas
- [ ] Tabelas `core.users`, `core.orders`, `core.financial_entries` existem
- [ ] Índices de performance criados (verificar com `\d core.financial_entries`)
- [ ] `core.alembic_version` contém `001_baseline`
- [ ] `alembic history` lista migration baseline
- [ ] Autogenerate detecta mudanças em models
- [ ] Downgrade remove alterações corretamente
- [ ] Stamp funciona em banco existente
- [ ] App FastAPI se conecta e funciona com schema Alembic

---

## 🎉 Conclusão

Se todos os testes passaram:

✅ **ETAPA 3B COMPLETA**

Você agora pode:
- Versionar mudanças no schema via Git
- Aplicar migrations em produção de forma controlada
- Reverter mudanças se necessário
- Gerar migrations automaticamente (autogenerate)
- Trabalhar em equipe com histórico de alterações

---

## 📚 Próximos Passos

1. Integrar migrations no pipeline de CI/CD
2. Criar migrations para novas features (ETAPA 4, 5, etc.)
3. Documentar processo de deploy com Alembic para equipe
4. Configurar backups automáticos antes de migrations críticas

---

**Documentação Relacionada:**
- `docs/ETAPA_3B_ALEMBIC_GUIA.md` (Guia completo)
- `scripts/migrate.ps1` (Script PowerShell)
- `scripts/migrate.sh` (Script Bash)

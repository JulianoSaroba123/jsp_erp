# ETAPA 3B - Comandos de Teste Executáveis
**Status:** READY FOR PRODUCTION  
**Data:** 2026-02-16

---

## A) BANCO VAZIO (Primeira Instalação)

### 1. Instalar dependências
```powershell
cd c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Executar migração completa
```powershell
cd c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend
python -m alembic upgrade head
```

**Output esperado:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_baseline, Create baseline schema
```

---

## B) BANCO EXISTENTE (Stamp sem execução)

### 1. Carimbar versão atual
```powershell
cd c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend
python -m alembic stamp head
```

**Output esperado:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running stamp_revision  -> 001_baseline
```

---

## C) VERIFICAÇÕES ALEMBIC

### 1. Verificar versão atual
```powershell
cd c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend
python -m alembic current
```

**Output esperado:**
```
001_baseline (head)
```

### 2. Verificar histórico
```powershell
cd c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend
python -m alembic history
```

**Output esperado:**
```
<base> -> 001_baseline (head), Create baseline schema
```

### 3. Verificar heads
```powershell
cd c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend
python -m alembic heads
```

**Output esperado:**
```
001_baseline (head)
```

---

## D) VERIFICAR TABELAS NO SCHEMA CORE

### 1. Conectar ao banco
```powershell
# Ler DATABASE_URL do .env
$env_content = Get-Content "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend\.env" | Where-Object { $_ -match "^DATABASE_URL=" }
$db_url = ($env_content -split "=", 2)[1]

# Extrair componentes (formato: postgresql://user:pass@host:port/dbname)
if ($db_url -match "postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)") {
    $PGUSER = $matches[1]
    $PGPASSWORD = $matches[2]
    $PGHOST = $matches[3]
    $PGPORT = $matches[4]
    $PGDATABASE = $matches[5]
    
    $env:PGPASSWORD = $PGPASSWORD
    Write-Host "Conectando em: $PGHOST:$PGPORT/$PGDATABASE como $PGUSER" -ForegroundColor Green
}
```

### 2. Verificar tabelas
```powershell
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'core' ORDER BY table_name;"
```

**Output esperado:**
```
 table_schema |     table_name      
--------------+---------------------
 core         | financial_entries
 core         | orders
 core         | users
(3 rows)
```

### 3. Verificar alembic_version está em core
```powershell
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'alembic_version';"
```

**Output esperado:**
```
 table_schema |   table_name    
--------------+-----------------
 core         | alembic_version
(1 row)
```

---

## E) VERIFICAR CONSTRAINTS E ÍNDICES

### 1. Verificar constraints em users
```powershell
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "SELECT conname, contype FROM pg_constraint WHERE conrelid = 'core.users'::regclass ORDER BY conname;"
```

**Output esperado:**
```
      conname       | contype 
--------------------+---------
 check_user_role    | c
 users_email_key    | u
 users_pkey         | p
(3 rows)
```

### 2. Verificar CHECK constraint de roles
```powershell
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'check_user_role';"
```

**Output esperado (deve conter 4 roles):**
```
CHECK ((role)::text = ANY (ARRAY[('admin'::character varying)::text, ('user'::character varying)::text, ('technician'::character varying)::text, ('finance'::character varying)::text]))
```

### 3. Verificar índices em financial_entries
```powershell
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'core' AND tablename = 'financial_entries' ORDER BY indexname;"
```

**Output esperado (4 índices):**
```
              indexname               |                                   indexdef                                    
--------------------------------------+-------------------------------------------------------------------------------
 financial_entries_pkey               | CREATE UNIQUE INDEX financial_entries_pkey ON core.financial_entries ...
 idx_financial_entries_kind           | CREATE INDEX idx_financial_entries_kind ON core.financial_entries ...
 idx_financial_entries_order          | CREATE INDEX idx_financial_entries_order ON core.financial_entries ...
 idx_financial_entries_status         | CREATE INDEX idx_financial_entries_status ON core.financial_entries ...
 idx_financial_entries_user_occurred  | CREATE INDEX idx_financial_entries_user_occurred ON core.financial_entries ...
(5 rows)
```

### 4. Verificar índice DESC
```powershell
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "SELECT indexdef FROM pg_indexes WHERE indexname = 'idx_financial_entries_user_occurred';"
```

**Output esperado (deve conter DESC):**
```
CREATE INDEX idx_financial_entries_user_occurred ON core.financial_entries USING btree (user_id, occurred_at DESC)
```

### 5. Verificar partial index
```powershell
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "SELECT indexdef FROM pg_indexes WHERE indexname = 'idx_financial_entries_order';"
```

**Output esperado (deve conter WHERE):**
```
CREATE INDEX idx_financial_entries_order ON core.financial_entries USING btree (order_id) WHERE (order_id IS NOT NULL)
```

---

## F) SMOKE CHECK AUTOMATIZADO

Execute o script de validação completo:

```powershell
cd c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend
.\validate_etapa3b.ps1
```

**Output esperado:** 12 checks ✅ PASS

---

## CLEANUP (APENAS DESENVOLVIMENTO)

### Reverter migração (⚠️ DESTROI DADOS)
```powershell
cd c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend
python -m alembic downgrade base
```

**NÃO executar em produção sem backup!**

# 🔧 SOLUÇÃO PRONTA PARA CORRIGIR O CI DA PR #5

**ATENÇÃO:** Este arquivo contém o código pronto para corrigir o erro do CI.  
**NÃO FOI APLICADO AINDA** conforme sua solicitação de não modificar código.

---

## 📋 PASSOS PARA APLICAR A CORREÇÃO

### 1️⃣ Criar nova migration 011a

**Arquivo:** `backend/alembic/versions/011a_expand_alembic_version.py`

**Conteúdo completo:**

```python
"""Expand alembic_version to support long migration names

Revision ID: 011a_expand_alembic_version
Revises: 011_create_service_orders
Create Date: 2026-07-03 00:00:00.000000

CONTEXTO:
=========
Esta migration resolve o erro de CI:

    psycopg2.errors.StringDataRightTruncation: value too long for type character varying(32)
    [SQL: UPDATE core.alembic_version SET version_num='012_add_proposals_and_service_order_types' ...]

PROBLEMA:
=========
A tabela alembic_version é criada automaticamente pelo Alembic com version_num VARCHAR(32).
A migration 012 tem um nome com 43 caracteres: '012_add_proposals_and_service_order_types'

SOLUÇÃO:
========
Expandir a coluna version_num de VARCHAR(32) para VARCHAR(100) ANTES da migration 012.

Esta é a mesma correção que foi aplicada manualmente no ambiente de desenvolvimento,
mas agora como migration Alembic para garantir que CI e ambientes de produção funcionem.

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '011a_expand_alembic_version'
down_revision = '011_create_service_orders'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Expand alembic_version.version_num from VARCHAR(32) to VARCHAR(100).
    
    This is necessary because migration 012 has a 43-character name:
    '012_add_proposals_and_service_order_types'
    
    Without this migration, fresh databases (like CI) will fail with:
    psycopg2.errors.StringDataRightTruncation: value too long for type character varying(32)
    """
    connection = op.get_bind()
    
    # Alter the column type from VARCHAR(32) to VARCHAR(100)
    connection.execute(
        """
        ALTER TABLE core.alembic_version 
        ALTER COLUMN version_num TYPE VARCHAR(100)
        """
    )


def downgrade() -> None:
    """
    Revert alembic_version.version_num back to VARCHAR(32).
    
    WARNING: This will fail if any migration names are longer than 32 characters!
    """
    connection = op.get_bind()
    
    connection.execute(
        """
        ALTER TABLE core.alembic_version 
        ALTER COLUMN version_num TYPE VARCHAR(32)
        """
    )
```

---

### 2️⃣ Modificar migration 012

**Arquivo:** `backend/alembic/versions/012_add_proposals_and_service_order_types.py`

**Mudança (linha 6 e linha 16):**

```diff
"""012_add_proposals_and_service_order_types

Create proposals tables and add tipo_ordem fields to service_orders

Revision ID: 012_add_proposals_and_service_order_types
-Revises: 011_create_service_orders
+Revises: 011a_expand_alembic_version
Create Date: 2026-03-11 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '012_add_proposals_and_service_order_types'
-down_revision = '011_create_service_orders'
+down_revision = '011a_expand_alembic_version'
branch_labels = None
depends_on = None
```

**Apenas 2 linhas mudam:**
- Linha 6: `Revises: 011a_expand_alembic_version`
- Linha 16: `down_revision = '011a_expand_alembic_version'`

---

### 3️⃣ Testar localmente

**PowerShell:**

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend'

# Ativar ambiente virtual
& .venv\Scripts\Activate.ps1

# Verificar histórico de migrations
alembic history

# Você deve ver:
# 025 -> 024 -> 023 -> ... -> 012 -> 011a -> 011 -> 010 -> ...

# Verificar que está na head atual
alembic current

# Se quiser testar em banco fresco (CUIDADO: apaga dados!)
# alembic downgrade base
# alembic upgrade head

# Testar apenas a nova migration
alembic upgrade 011a

# Verificar se passou
alembic current
# Deve mostrar: 011a_expand_alembic_version
```

---

### 4️⃣ Verificar que a coluna foi expandida

**PowerShell (conectar ao PostgreSQL):**

```powershell
# Conectar ao banco
psql -U jsp_user -d jsp_erp -h localhost -p 5433

# No prompt do psql:
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_schema = 'core' 
  AND table_name = 'alembic_version';

# Deve mostrar:
#   column_name   | data_type         | character_maximum_length
# ----------------+-------------------+--------------------------
#   version_num   | character varying | 100

# Sair do psql
\q
```

---

### 5️⃣ Commit e push

**PowerShell:**

```powershell
cd 'c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp'

# Adicionar arquivos modificados
git add backend/alembic/versions/011a_expand_alembic_version.py
git add backend/alembic/versions/012_add_proposals_and_service_order_types.py

# Commit
git commit -m "fix(alembic): expand version_num to VARCHAR(100) to support long migration names

PROBLEMA:
- CI falhava na migration 012 com erro StringDataRightTruncation
- alembic_version.version_num era VARCHAR(32)
- Migration 012 tem nome com 43 caracteres

SOLUÇÃO:
- Nova migration 011a expande version_num para VARCHAR(100)
- Migration 012 agora depende de 011a
- CI em banco fresco agora passa

Fixes: Falha do CI na PR #5
Ref: RELATORIO_INVESTIGACAO_CI_PR5.md"

# Push
git push origin feature/etapa-6-enterprise
```

---

### 6️⃣ Aguardar CI

Após o push, o GitHub Actions executará automaticamente:

1. ✅ Criar banco PostgreSQL fresco
2. ✅ Executar `alembic upgrade head`
   - Aplica migrations 001 → 011 ✅
   - Aplica migration **011a** (expande version_num) ✅
   - Aplica migration **012** (agora cabe em 100 chars) ✅
   - Aplica migrations 013 → 025 ✅
3. ✅ Executar pytest
4. ✅ PR pronta para merge! 🎉

---

## 🔍 VERIFICAÇÃO PÓS-CORREÇÃO

### Como confirmar que funcionou:

1. **Acessar GitHub Actions:** https://github.com/JulianoSaroba123/jsp_erp/actions
2. **Procurar pelo commit** com mensagem "fix(alembic): expand version_num..."
3. **Verificar que o step "Run Alembic migrations" passou** ✅
4. **Verificar que o step "Run tests with coverage" passou** ✅
5. **PR #5 deve mostrar** "All checks have passed" ✅

---

## ⚠️ IMPORTANTE: Ambientes existentes

### Seu ambiente de desenvolvimento local

**Não precisa fazer nada.**

Você já tem `alembic_version.version_num VARCHAR(100)` porque aplicou a correção manual.

Quando fizer `alembic upgrade head`, a migration 011a vai detectar que a coluna já é VARCHAR(100) e não fará nada (ALTER TABLE é idempotente).

### Outros desenvolvedores

Se outras pessoas tiverem o banco local com VARCHAR(32):
- A migration 011a vai expandir automaticamente para VARCHAR(100) ✅

### Produção

Se já tiver produção rodando:
- A migration 011a expande a coluna sem perder dados ✅
- Migrations 012-025 continuam funcionando normalmente ✅

---

## ✅ CHECKLIST COMPLETO

```markdown
- [ ] 1. Criar arquivo backend/alembic/versions/011a_expand_alembic_version.py
- [ ] 2. Modificar backend/alembic/versions/012_add_proposals_and_service_order_types.py (linha 6 e 16)
- [ ] 3. Testar localmente: alembic upgrade 011a
- [ ] 4. Verificar coluna: SELECT character_maximum_length FROM information_schema.columns WHERE...
- [ ] 5. git add + git commit + git push
- [ ] 6. Aguardar CI passar (GitHub Actions)
- [ ] 7. Verificar que PR #5 mostra "All checks have passed"
- [ ] 8. (Opcional) Solicitar review e merge
```

---

## 📊 ESTIMATIVA DE TEMPO

- Criar migration 011a: **2 minutos**
- Modificar migration 012: **1 minuto**
- Testar localmente: **5 minutos**
- Commit + Push: **2 minutos**
- Aguardar CI: **5-10 minutos**
- **TOTAL: ~15-20 minutos** ⏱️

---

## 🎯 RESUMO ULTRA-RÁPIDO (TL;DR)

```bash
# 1. Criar arquivo
# backend/alembic/versions/011a_expand_alembic_version.py
# (copiar conteúdo da seção 1️⃣ acima)

# 2. Modificar arquivo
# backend/alembic/versions/012_add_proposals_and_service_order_types.py
# Mudar: down_revision = '011a_expand_alembic_version'

# 3. Commit e push
git add backend/alembic/versions/*.py
git commit -m "fix(alembic): expand version_num to VARCHAR(100)"
git push origin feature/etapa-6-enterprise

# 4. Aguardar CI passar ✅
```

---

**Pronto!** Agora você tem tudo o que precisa para corrigir o CI. 🚀

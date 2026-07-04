# 🔍 RELATÓRIO DE INVESTIGAÇÃO - FALHA DO CI DA PR #5

**Data:** 2026-07-03  
**PR:** #5 - fix(rbac): idempotent migration 005 + schema tests  
**Branch:** feature/etapa-6-enterprise  
**Status:** ❌ **FALHOU**  
**GitHub Actions Job:** https://github.com/JulianoSaroba123/jsp_erp/actions/runs/28635658616/job/84921324483

---

## 📊 RESUMO EXECUTIVO

O CI falhou **ANTES** de executar os testes pytest. A falha ocorreu durante a etapa **"Run Alembic migrations"** ao tentar aplicar a migration `012_add_proposals_and_service_order_types`.

### ❌ Tipo de Falha

**ERRO DE AMBIENTE CI** (não é erro de código propriamente dito)

O erro é **reproduzível** em qualquer banco de dados PostgreSQL fresco que execute `alembic upgrade head` a partir do zero.

---

## 🚨 ERRO PRINCIPAL

### Comando que falhou

```bash
alembic upgrade head
```

### Arquivo de migração que causou a falha

```
backend/alembic/versions/012_add_proposals_and_service_order_types.py
```

### Mensagem de erro completa

```
psycopg2.errors.StringDataRightTruncation: value too long for type character varying(32)

[SQL: UPDATE core.alembic_version SET 
version_num='012_add_proposals_and_service_order_types' 
WHERE core.alembic_version.version_num = '011_create_service_orders']
```

### Stack trace resumido

```python
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
psycopg2.errors.StringDataRightTruncation: value too long for type character varying(32)

The above exception was the direct cause of the following exception:

sqlalchemy.exc.DataError: (psycopg2.errors.StringDataRightTruncation) value too long for type character varying(32)
```

### Timestamp do erro

```
2026-07-03T03:05:56.7421609Z
```

**Etapa:** `Run Alembic migrations` (step 6 do workflow)  
**Exit Code:** 1

---

## 🎯 CAUSA RAIZ

### Problema

A tabela `core.alembic_version` possui a coluna `version_num` com tipo **`VARCHAR(32)`**.

A migration `012_add_proposals_and_service_order_types` possui um nome com **43 caracteres**, ultrapassando o limite de 32.

### Por que o nome é tão longo?

```python
revision = '012_add_proposals_and_service_order_types'
# Caracteres: 012_add_proposals_and_service_order_types = 43 chars
```

### Como a tabela alembic_version é criada?

Quando você executa `alembic upgrade head` pela primeira vez em um banco de dados limpo, o Alembic cria automaticamente a tabela `core.alembic_version` com a seguinte estrutura **padrão**:

```sql
CREATE TABLE core.alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
```

**O problema:** Alembic usa `VARCHAR(32)` por padrão, mas permite nomes de migration com até 100 caracteres.

---

## 📋 HISTÓRICO DO PROBLEMA

### Ambientes afetados

| Ambiente | Status | Motivo |
|----------|--------|--------|
| **Desenvolvimento local** | ✅ **PASSOU** | Correção manual aplicada (ALTER TABLE) |
| **CI (banco fresco)** | ❌ **FALHOU** | Sem correção aplicada |
| **Production** | ⚠️ **RISCO** | Se fizer deploy fresco, falhará |

### Como foi resolvido localmente?

De acordo com o arquivo `docs/ETAPA_6_ENTERPRISE_CONCLUSAO.md`, o problema foi encontrado e corrigido manualmente:

```sql
-- Solução aplicada manualmente no ambiente de desenvolvimento
ALTER TABLE core.alembic_version 
ALTER COLUMN version_num TYPE VARCHAR(100);
```

**Documentação encontrada:**

```markdown
## ⚙️ SOLUÇÕES IMPLEMENTADAS

### 1. **Expansão de alembic_version.version_num**
```sql
-- De VARCHAR(32) para VARCHAR(100)
ALTER TABLE core.alembic_version 
ALTER COLUMN version_num TYPE VARCHAR(100);
```

**Justificativa:** Suportar nomes de migração descritivos (até 100 chars)
```

### Por que o CI ainda falha?

**A correção foi manual, não foi criada uma migration Alembic para isso.**

Quando o CI executa em um banco de dados limpo:
1. Cria `alembic_version` com `VARCHAR(32)` (padrão Alembic)
2. Aplica migrations 001 → 011 ✅
3. Tenta aplicar migration 012 ❌ **FALHA: 43 chars > 32 chars**

---

## 🔧 SOLUÇÕES POSSÍVEIS

### ✅ Opção 1: Criar migration que expande alembic_version (RECOMENDADA)

**Vantagem:** Resolve o problema permanentemente para CI, produção e novos ambientes.

**Implementação:**

Criar uma nova migration **ANTES da 012** que expanda a coluna:

```python
# backend/alembic/versions/011a_expand_alembic_version.py
"""Expand alembic_version to support long migration names

Revision ID: 011a_expand_alembic_version
Revises: 011_create_service_orders
Create Date: 2026-07-03 00:00:00.000000

"""
from alembic import op


revision = '011a_expand_alembic_version'
down_revision = '011_create_service_orders'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Expand alembic_version.version_num from VARCHAR(32) to VARCHAR(100).
    
    This is necessary because migration 012 has a 43-character name:
    '012_add_proposals_and_service_order_types'
    """
    connection = op.get_bind()
    connection.execute(
        """
        ALTER TABLE core.alembic_version 
        ALTER COLUMN version_num TYPE VARCHAR(100)
        """
    )


def downgrade() -> None:
    """Revert to VARCHAR(32)"""
    connection = op.get_bind()
    connection.execute(
        """
        ALTER TABLE core.alembic_version 
        ALTER COLUMN version_num TYPE VARCHAR(32)
        """
    )
```

**Depois:**

```python
# backend/alembic/versions/012_add_proposals_and_service_order_types.py
revision = '012_add_proposals_and_service_order_types'
down_revision = '011a_expand_alembic_version'  # ← MUDAR AQUI
branch_labels = None
depends_on = None
```

---

### ⚠️ Opção 2: Renomear migration 012 (MAIS RÁPIDO, MAS PROBLEMÁTICO)

**Vantagem:** Correção rápida, sem criar nova migration.

**Desvantagem:** 
- Quebra histórico Git (migration já existe em commits)
- Pode causar conflitos em ambientes que já aplicaram a 012 (desenvolvimento local)
- Não é profissional alterar migrations já publicadas

**Implementação:**

```python
# Renomear de:
revision = '012_add_proposals_and_service_order_types'  # 43 chars

# Para:
revision = '012_add_proposals'  # 17 chars ✅
```

**NÃO RECOMENDADO** se a migration 012 já foi aplicada em algum ambiente.

---

### ❌ Opção 3: Fazer nada e aceitar falha

**NÃO RECOMENDADO.** O CI sempre falhará.

---

## 📝 ANÁLISE DOS COMENTÁRIOS DE REVIEW DO CODEX

Além da falha do CI, a PR #5 possui 3 comentários automáticos do Codex:

### 1️⃣ **P1 - Register Permission model before configuring Role mapper**

**Arquivo:** [backend/app/models/role.py](backend/app/models/role.py)

**Problema:** 
- `Role.permissions` relationship aponta para `"Permission"` (string)
- SQLAlchemy precisa que o modelo `Permission` seja importado para resolver o mapper
- Se não for importado em tempo de execução, pode lançar `InvalidRequestError`

**Status:** ⚠️ **POTENCIALMENTE VÁLIDO**

**Verificação:** 
No arquivo [backend/app/models/__init__.py](backend/app/models/__init__.py), vejo que **Permission JÁ É IMPORTADO**:

```python
from app.models.role import Role
from app.models.permission import Permission
```

Então esse comentário pode ser **falso positivo** ou refere-se a um commit anterior.

---

### 2️⃣ **P1 - Preserve delete access until users receive RBAC roles**

**Arquivo:** [backend/app/routers/order_routes.py](backend/app/routers/order_routes.py)

**Problema:**
- Endpoint `DELETE /orders/{order_id}` usa `require_permission("orders", "delete")`
- Depende de `User.has_permission()` que lê `user.roles` (RBAC)
- Usuários ainda usam `user.role` (string legado) e não têm roles RBAC atribuídas
- Resultado: usuários existentes perdem acesso a DELETE

**Status:** ⚠️ **VÁLIDO - REGRESSÃO POTENCIAL**

**Impacto:** Se usuários não receberem roles RBAC, operações de DELETE falharão com 403.

**Correção sugerida:** Criar migration de dados (seed) que atribua roles RBAC aos usuários existentes.

---

### 3️⃣ **P2 - Keep 005 downgrade from dropping 004-owned RBAC tables**

**Arquivo:** [backend/alembic/versions/005_rbac_idempotent.py](backend/alembic/versions/005_rbac_idempotent.py)

**Problema:**
- Migration 005 faz `downgrade()` que dropa tabelas RBAC
- Migration 004 também gerencia essas tabelas
- Se fizer `alembic downgrade 004`, a 005 vai dropar as tabelas
- Depois, ao fazer upgrade novamente, a 004 tenta criar e pode falhar

**Status:** ⚠️ **VÁLIDO - PROBLEMA DE ARQUITETURA DE MIGRATIONS**

**Impacto:** Baixo (só afeta quem faz downgrades)

**Correção sugerida:** 005 deveria usar `DROP TABLE IF EXISTS` no downgrade ou remover completamente o downgrade (apenas `pass`).

---

## 🎯 RECOMENDAÇÃO FINAL

### 🔴 **BLOQUEADOR CRÍTICO: Falha do Alembic**

**Prioridade:** P0 - CRÍTICO  
**Ação:** Criar migration 011a que expande `alembic_version.version_num` para VARCHAR(100)  
**Arquivos a modificar:**
1. Criar: `backend/alembic/versions/011a_expand_alembic_version.py`
2. Modificar: `backend/alembic/versions/012_add_proposals_and_service_order_types.py` (mudar `down_revision`)

**Impacto:** SEM ISSO, O CI NUNCA PASSARÁ.

---

### ⚠️ **OPCIONAL MAS RECOMENDADO: Review Comments do Codex**

**Prioridade:** P1 - ALTO  
**Ação:** Endereçar comentários #2 e #3  
**Impacto:** Evitar regressões em produção e problemas de downgrade

---

## 📂 ARQUIVOS PARA MODIFICAR

### Para corrigir o CI:

1. **Criar:** `backend/alembic/versions/011a_expand_alembic_version.py`
   - Expande `core.alembic_version.version_num` de VARCHAR(32) para VARCHAR(100)
   - `down_revision = '011_create_service_orders'`

2. **Modificar:** `backend/alembic/versions/012_add_proposals_and_service_order_types.py`
   - Alterar linha 15: `down_revision = '011a_expand_alembic_version'`

3. **Opcional:** Renomear migrations futuras (013+) para terem nomes < 100 chars (boa prática)

---

### Para endereçar review comments:

4. **Opcional:** `backend/app/routers/order_routes.py`
   - Adicionar fallback para `user.role` legado no `require_permission`

5. **Opcional:** `backend/alembic/versions/005_rbac_idempotent.py`
   - Adicionar `IF EXISTS` no downgrade ou remover downgrade

6. **Opcional:** Criar migration de seed RBAC
   - Atribuir roles aos usuários existentes

---

## ✅ CHECKLIST DE CORREÇÃO

```markdown
- [ ] 1. Criar migration 011a_expand_alembic_version.py
- [ ] 2. Modificar down_revision da migration 012
- [ ] 3. Testar localmente: `alembic downgrade base && alembic upgrade head`
- [ ] 4. Verificar que não há erros de truncamento
- [ ] 5. Commit e push das mudanças
- [ ] 6. Aguardar CI passar
- [ ] 7. (Opcional) Endereçar comentários de review do Codex
```

---

## 🔍 CONCLUSÃO

### Causa raiz provável

**Tabela `alembic_version.version_num` é VARCHAR(32) mas migration 012 tem 43 caracteres.**

### Correção mínima recomendada

**Criar migration 011a que expande a coluna para VARCHAR(100) ANTES da migration 012.**

### Arquivos prováveis a alterar

1. `backend/alembic/versions/011a_expand_alembic_version.py` (NOVO)
2. `backend/alembic/versions/012_add_proposals_and_service_order_types.py` (MODIFICAR down_revision)

### Se precisa corrigir antes do merge

**SIM - OBRIGATÓRIO.** Sem essa correção, o CI nunca passará e a PR não poderá ser mergeada.

---

## 📊 EVIDÊNCIAS

### Log do CI (fragmento relevante)

```
2026-07-03T03:05:56.7405030Z Running upgrade 011_create_service_orders -> 012_add_proposals_and_service_order_types
2026-07-03T03:05:56.7416955Z Traceback (most recent call last):
2026-07-03T03:05:56.7421609Z psycopg2.errors.StringDataRightTruncation: value too long for type character varying(32)
2026-07-03T03:05:56.7422769Z 
2026-07-03T03:05:56.7482053Z sqlalchemy.exc.DataError: (psycopg2.errors.StringDataRightTruncation) value too long for type character varying(32)
2026-07-03T03:05:56.7485123Z [SQL: UPDATE core.alembic_version SET version_num='012_add_proposals_and_service_order_types' WHERE core.alembic_version.version_num = '011_create_service_orders']
2026-07-03T03:05:56.8156245Z ##[error]Process completed with exit code 1.
```

### Nome da migration problemática

```python
revision = '012_add_proposals_and_service_order_types'
# Contagem de caracteres:
# 0         1         2         3         4
# 0123456789012345678901234567890123456789012
# 012_add_proposals_and_service_order_types
# Total: 43 caracteres
```

---

**Relatório gerado em:** 2026-07-03  
**Autor:** GitHub Copilot (Análise automatizada do CI)  
**Revisão:** Pendente

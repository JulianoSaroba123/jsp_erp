# ETAPA 3B - Alembic Database Migrations

**Guia Completo de Configuração e Uso**

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Instalação](#instalação)
4. [Configuração](#configuração)
5. [Uso Básico](#uso-básico)
6. [Cenários Comuns](#cenários-comuns)
7. [Troubleshooting](#troubleshooting)
8. [Boas Práticas](#boas-práticas)

---

## Visão Geral

### O que é Alembic?

Alembic é uma ferramenta de **database migrations** para SQLAlchemy. Permite:

- ✅ Versionamento do schema do banco de dados
- ✅ Aplicar mudanças incrementais (migrations)
- ✅ Reverter mudanças (rollback)
- ✅ Rastrear histórico de alterações
- ✅ Gerar migrations automaticamente (autogenerate)
- ✅ Trabalhar em equipe com controle de versão (Git)

### Por que usar Alembic?

**Antes (Scripts SQL manuais):**
```sql
-- 01_structure.sql
-- 02_seed_users.sql
-- 03_orders.sql
-- ...
```
- ❌ Difícil rastrear qual script foi aplicado
- ❌ Sem rollback automático
- ❌ Conflitos em equipes (quem aplicou o quê?)
- ❌ Risco de aplicar script duas vezes

**Depois (Alembic):**
```bash
alembic upgrade head    # Aplica todas migrations pendentes
alembic current         # Mostra versão atual
alembic downgrade -1    # Reverte última migration
```
- ✅ Rastreamento automático de versão (tabela `core.alembic_version`)
- ✅ Rollback simplificado
- ✅ Histórico completo em Git
- ✅ Idempotência garantida

---

## Arquitetura

### Estrutura de Arquivos

```
backend/
├── alembic/
│   ├── versions/
│   │   └── 001_baseline.py         # Migration inicial
│   ├── env.py                       # Configuração do ambiente
│   └── script.py.mako               # Template para novas migrations
├── alembic.ini                      # Configuração principal
├── app/
│   ├── models/                      # Models SQLAlchemy (fonte da verdade)
│   │   ├── user.py
│   │   ├── order.py
│   │   └── financial_entry.py
│   ├── database.py                  # Base e conexão
│   └── config.py                    # DATABASE_URL (lê do .env)
└── .env                             # DATABASE_URL

scripts/
├── migrate.ps1                      # Script utilitário (Windows)
└── migrate.sh                       # Script utilitário (Linux/macOS)
```

### Fluxo de Dados

```
┌─────────────┐
│   Models    │  (app/models/*.py)
│ SQLAlchemy  │  ← Fonte da verdade do schema
└──────┬──────┘
       │
       │ metadata
       │
┌──────▼──────────┐
│  Alembic env.py │  Lê models + DATABASE_URL
└──────┬──────────┘
       │
       │ autogenerate
       │
┌──────▼──────────┐
│   Migration     │  versions/001_baseline.py
│   (Python)      │  ← upgrade() / downgrade()
└──────┬──────────┘
       │
       │ upgrade head
       │
┌──────▼──────────┐
│  PostgreSQL DB  │  Schema "core" + alembic_version
└─────────────────┘
```

### Schema "core" e Versionamento

Todas as tabelas e a tabela de controle do Alembic ficam no schema **`core`**:

```sql
-- Tabelas do app
core.users
core.orders
core.financial_entries

-- Tabela de controle do Alembic
core.alembic_version  ← Armazena versão atual da migration
```

---

## Instalação

### 1. Instalar Dependências

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

Isso instala:
- `alembic` (migrations)
- `sqlalchemy` (ORM)
- `psycopg[binary]` (driver PostgreSQL)
- `python-dotenv` (lê .env)

### 2. Configurar .env

Certifique-se de que o arquivo `backend/.env` contém:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/jsp_erp
SECRET_KEY=your-secret-key-here
```

**IMPORTANTE:** O Alembic usa o mesmo `DATABASE_URL` do app (via `app/config.py`).

### 3. Verificar Instalação

```bash
cd backend
python -m alembic --version
```

Saída esperada:
```
alembic 1.x.x
```

---

## Configuração

### Arquivos Principais

#### 1. `alembic.ini`

Configuração global do Alembic:

```ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
version_locations = %(here)s/alembic/versions
```

**Nota:** `sqlalchemy.url` é **sobrescrito** por `env.py` com o valor do `.env`.

#### 2. `alembic/env.py`

Configuração dinâmica que:

✅ Lê `DATABASE_URL` do `.env`  
✅ Importa models SQLAlchemy (User, Order, FinancialEntry)  
✅ Configura `target_metadata = Base.metadata`  
✅ Define `version_table_schema="core"`  
✅ Ativa `include_schemas=True`  

**Snippet crítico:**
```python
from app.config import DATABASE_URL
from app.database import Base
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry

config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = Base.metadata
```

#### 3. `alembic/versions/001_baseline.py`

Migration inicial que cria:

- Schema `core`
- Tabela `core.users` (com constraints, índices)
- Tabela `core.orders` (FK para users)
- Tabela `core.financial_entries` (FKs, checks, índices de performance)

**Estrutura:**
```python
def upgrade() -> None:
    # Criar schema
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    
    # Criar tabelas
    op.create_table('users', ...)
    op.create_table('orders', ...)
    op.create_table('financial_entries', ...)
    
    # Criar índices
    op.create_index('idx_financial_entries_user_occurred', ...)

def downgrade() -> None:
    # Reverter (DROP tabelas + schema)
    op.drop_table('financial_entries', schema='core')
    op.drop_table('orders', schema='core')
    op.drop_table('users', schema='core')
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")
```

---

## Uso Básico

### Scripts Utilitários

Para facilitar, use os scripts `migrate.ps1` (Windows) ou `migrate.sh` (Linux/macOS):

**Windows (PowerShell):**
```powershell
.\scripts\migrate.ps1 current          # Ver versão atual
.\scripts\migrate.ps1 upgrade          # Aplicar migrations
.\scripts\migrate.ps1 downgrade -1     # Reverter última
.\scripts\migrate.ps1 history          # Ver histórico
.\scripts\migrate.ps1 stamp head       # Marcar como aplicada (banco existente)
```

**Linux/macOS (Bash):**
```bash
./scripts/migrate.sh current
./scripts/migrate.sh upgrade
./scripts/migrate.sh downgrade -1
./scripts/migrate.sh history
./scripts/migrate.sh stamp head
```

### Comandos Alembic Diretos

Se preferir usar Alembic diretamente:

```bash
cd backend

# Ver versão atual
python -m alembic current

# Aplicar todas migrations pendentes
python -m alembic upgrade head

# Reverter última migration
python -m alembic downgrade -1

# Ver histórico completo
python -m alembic history --verbose

# Marcar como aplicada (sem executar DDL)
python -m alembic stamp head

# Criar nova migration (autogenerate)
python -m alembic revision --autogenerate -m "add_new_table"
```

---

## Cenários Comuns

### Cenário 1: Banco de Dados Vazio (Novo Projeto)

**Situação:** Banco PostgreSQL recém-criado, sem tabelas.

**Passos:**

1. Configurar `.env` com `DATABASE_URL`
2. Aplicar migration baseline:

```bash
cd backend
python -m alembic upgrade head
```

**Resultado:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_baseline, baseline_schema_core_users_orders_financial
```

3. Verificar:

```bash
python -m alembic current
```

**Saída:**
```
001_baseline (head)
```

4. Confirmar no banco:

```sql
-- Conectar ao PostgreSQL
\c jsp_erp

-- Ver schemas
\dn

-- Ver tabelas
\dt core.*

-- Ver versão do Alembic
SELECT * FROM core.alembic_version;
```

**Esperado:**
```
 version_num 
-------------
 001_baseline
```

---

### Cenário 2: Banco Existente (Migração de Scripts SQL para Alembic)

**Situação:** Banco já possui tabelas criadas via scripts SQL (`01_structure.sql`, etc.).

**⚠️ IMPORTANTE:** Não execute `alembic upgrade head` — isso tentará recriar as tabelas e falhará!

**Solução: Stamp (Marcar como Aplicada)**

1. Verificar que as tabelas existem:

```sql
\dt core.*
```

Esperado:
```
         List of tables
 Schema |       Name       | Type  | Owner 
--------+------------------+-------+-------
 core   | users            | table | ...
 core   | orders           | table | ...
 core   | financial_entries| table | ...
```

2. Marcar o banco como na versão `001_baseline` (sem executar DDL):

```bash
cd backend
python -m alembic stamp 001_baseline
```

ou

```bash
.\scripts\migrate.ps1 stamp head
```

**Resultado:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Stamping revision table with 001_baseline
```

3. Confirmar:

```bash
python -m alembic current
```

**Saída:**
```
001_baseline (head)
```

4. Verificar no banco:

```sql
SELECT * FROM core.alembic_version;
```

**Esperado:**
```
 version_num 
-------------
 001_baseline
```

**Pronto!** Agora o Alembic reconhece que o schema está na versão baseline. Futuras migrations serão aplicadas normalmente.

---

### Cenário 3: Criar Nova Migration (Autogenerate)

**Situação:** Você adicionou um novo model SQLAlchemy (ex: `app/models/invoice.py`) e quer gerar a migration automaticamente.

**Passos:**

1. Criar/editar model:

```python
# app/models/invoice.py
from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = {"schema": "core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    number = Column(String(50), nullable=False, unique=True)
    amount = Column(Numeric(12, 2), nullable=False)
```

2. Importar model em `app/models/__init__.py`:

```python
from app.models.invoice import Invoice
```

3. Importar em `alembic/env.py` (para autogenerate detectar):

```python
from app.models.invoice import Invoice
```

4. Gerar migration:

```bash
cd backend
python -m alembic revision --autogenerate -m "add_invoices_table"
```

ou

```bash
.\scripts\migrate.ps1 revision -m "add_invoices_table"
```

**Resultado:**
```
INFO  [alembic.autogenerate.compare] Detected added table 'invoices'
  Generating /.../versions/20260216_1430_002_add_invoices_table.py ... done
```

5. **REVISAR A MIGRATION GERADA** (crítico!):

Abrir `alembic/versions/002_add_invoices_table.py` e verificar:

- ✅ Tabela criada no schema `core`
- ✅ Constraints corretas
- ✅ Índices necessários
- ✅ Comentários (se relevante)

6. Aplicar migration:

```bash
python -m alembic upgrade head
```

7. Confirmar:

```bash
python -m alembic current
```

**Saída:**
```
002_add_invoices_table (head)
```

---

### Cenário 4: Reverter Migration (Rollback)

**Situação:** A última migration causou problema em produção e você precisa reverter.

**Passos:**

1. Ver versão atual:

```bash
python -m alembic current
```

**Saída:**
```
002_add_invoices_table (head)
```

2. Reverter última migration:

```bash
python -m alembic downgrade -1
```

ou

```bash
.\scripts\migrate.ps1 downgrade -1
```

**⚠️ O script pedirá confirmação:**
```
⚠️  ATENÇÃO: Downgrade pode remover dados!
Confirma downgrade para '-1'? (s/N)
```

Digite `s` e pressione Enter.

**Resultado:**
```
INFO  [alembic.runtime.migration] Running downgrade 002 -> 001, add_invoices_table
```

3. Confirmar:

```bash
python -m alembic current
```

**Saída:**
```
001_baseline (head)
```

**Nota:** A tabela `core.invoices` foi removida.

---

### Cenário 5: Rollback para Versão Específica

Para reverter para uma versão específica (não apenas -1):

```bash
# Ver histórico
python -m alembic history

# Reverter para 001_baseline
python -m alembic downgrade 001_baseline
```

---

## Troubleshooting

### Erro: "relation 'core.alembic_version' does not exist"

**Causa:** Banco de dados não foi inicializado com Alembic.

**Solução:**

Se o banco **está vazio**:
```bash
python -m alembic upgrade head
```

Se o banco **já tem tabelas** (via scripts SQL):
```bash
python -m alembic stamp 001_baseline
```

---

### Erro: "Target database is not up to date"

**Causa:** Migrations pendentes.

**Solução:**
```bash
# Ver migrations pendentes
python -m alembic history

# Ver versão atual
python -m alembic current

# Aplicar pendentes
python -m alembic upgrade head
```

---

### Erro: "relation 'core.users' already exists"

**Causa:** Tentou executar `alembic upgrade head` em banco que já tem as tabelas.

**Solução:**

1. Reverter migration (se possível):
```bash
python -m alembic downgrade base
```

2. Ou marcar como aplicada (stamp):
```bash
python -m alembic stamp 001_baseline
```

---

### Erro: "Can't locate revision identified by '001_baseline'"

**Causa:** Arquivo de migration não encontrado ou corrompido.

**Solução:**

1. Verificar se existe:
```bash
ls backend/alembic/versions/
```

Deve conter: `001_baseline.py`

2. Se não existir, restaurar do repositório:
```bash
git checkout backend/alembic/versions/001_baseline.py
```

---

### Erro: "ModuleNotFoundError: No module named 'app'"

**Causa:** `alembic/env.py` não consegue importar módulos do app.

**Solução:**

1. Verificar que está executando do diretório `backend/`:
```bash
cd backend
python -m alembic current
```

2. Verificar que `alembic/env.py` adiciona o path corretamente:
```python
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))
```

---

### Erro: "sqlalchemy.exc.OperationalError: (psycopg.OperationalError) connection failed"

**Causa:** DATABASE_URL inválido ou banco não acessível.

**Solução:**

1. Verificar `.env`:
```bash
cat backend/.env | grep DATABASE_URL
```

2. Testar conexão:
```python
python -c "from app.config import DATABASE_URL; print(DATABASE_URL)"
```

3. Verificar que PostgreSQL está rodando:
```bash
# Windows
docker ps  # Se usando Docker

# Linux
sudo systemctl status postgresql
```

---

### Autogenerate não detecta mudanças

**Causa:** Model não foi importado em `alembic/env.py`.

**Solução:**

Adicionar import explícito em `alembic/env.py`:
```python
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry
from app.models.invoice import Invoice  # ← Adicionar novo model
```

---

### Migration gerada com lixo (operações desnecessárias)

**Causa:** Autogenerate detecta diferenças entre models e banco que não são reais (ex: ordem de colunas, tipos equivalentes).

**Solução:**

1. **Sempre revisar** a migration gerada antes de aplicar.

2. Editar manualmente e remover operações desnecessárias.

3. Configurar `compare_type=False` em `env.py` se tipos de coluna causarem falsos positivos:
```python
context.configure(
    ...
    compare_type=False,  # Não comparar tipos de SQL
)
```

---

## Boas Práticas

### 1. ✅ Sempre Revisar Migrations Geradas

**Nunca aplique migrations geradas automaticamente sem revisar!**

```bash
# Gerar
python -m alembic revision --autogenerate -m "add_feature"

# REVISAR o arquivo em alembic/versions/
# Verificar:
# - Schema correto (core)
# - Constraints adequados
# - Índices de performance
# - Comentários (se necessário)

# Só então aplicar
python -m alembic upgrade head
```

---

### 2. ✅ Commits Atômicos

Cada migration deve ter um commit dedicado no Git:

```bash
# Criar migration
python -m alembic revision --autogenerate -m "add_invoices"

# Revisar e editar se necessário

# Commit
git add backend/alembic/versions/002_add_invoices.py
git commit -m "feat: add invoices table migration (ETAPA 3B)"
```

**Benefício:** Facilita rollback no Git se a migration tiver problemas.

---

### 3. ✅ Testar Upgrade E Downgrade

Antes de fazer merge/deploy, testar ambas direções:

```bash
# Aplicar
python -m alembic upgrade head

# Testar app (endpoints funcionam?)

# Reverter
python -m alembic downgrade -1

# Testar app (voltou ao estado anterior?)

# Reaplicar
python -m alembic upgrade head
```

---

### 4. ✅ Migrations Pequenas e Incrementais

**Ruim (monolítico):**
```
002_big_refactor.py  ← Cria 5 tabelas, remove 3, altera 10 colunas
```

**Bom (incremental):**
```
002_add_invoices.py
003_add_payments.py
004_alter_users_add_phone.py
```

**Benefício:** Rollback mais granular e menos risco.

---

### 5. ✅ Documentar Migrations Complexas

Se a migration for não-trivial, adicionar comentários:

```python
def upgrade() -> None:
    """
    Adiciona campo 'phone' à tabela users.
    
    ATENÇÃO:
    - Campo é nullable inicialmente (dados existentes ficam NULL)
    - Após deploy, rodar script de backfill para popular phones
    - Em migration futura (005), tornar NOT NULL
    """
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True), schema='core')
```

---

### 6. ✅ Usar Stamp para Adoção Gradual

Se migrando de scripts SQL para Alembic:

1. Criar baseline que reflete estado atual
2. Fazer stamp em produção:
```bash
python -m alembic stamp 001_baseline
```
3. A partir daí, todas mudanças via Alembic

**Benefício:** Sem downtime e sem conflito com scripts SQL existentes.

---

### 7. ✅ Backup Antes de Downgrade

**Sempre faça backup do banco antes de downgrade em produção:**

```bash
# Backup
pg_dump -U user -d jsp_erp -F c -f backup_before_downgrade.dump

# Downgrade
python -m alembic downgrade -1

# Se der problema, restaurar
pg_restore -U user -d jsp_erp -F c backup_before_downgrade.dump
```

---

### 8. ✅ CI/CD: Aplicar Migrations Automaticamente

**Exemplo de pipeline (GitHub Actions):**

```yaml
# .github/workflows/deploy.yml
- name: Run Migrations
  run: |
    cd backend
    python -m alembic upgrade head
```

**Ou manual com aprovação:**
```yaml
- name: Run Migrations
  run: |
    cd backend
    python -m alembic current
    python -m alembic upgrade head
  if: github.event_name == 'release'
```

---

## Referências

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## Próximos Passos

1. ✅ Executar comandos de teste (ver `COMANDOS_TESTE_ETAPA3B.md`)
2. ✅ Criar primeira migration customizada (adicionar campo/tabela)
3. ✅ Integrar migrations no fluxo de deploy/CI
4. ✅ Documentar processo para equipe

---

**ETAPA 3B COMPLETA** 🎉

Alembic configurado e pronto para uso!

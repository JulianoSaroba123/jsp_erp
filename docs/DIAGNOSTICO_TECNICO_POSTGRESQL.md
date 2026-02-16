# DIAGNÓSTICO TÉCNICO - PostgreSQL Docker vs Localhost

## Resumo Executivo

**Problema relatado:** Tabela `core.orders` não existia quando FastAPI tentava acessá-la.

**Causa raiz identificada:** Scripts SQL foram executados em **contexto diferente** - provavelmente no banco default 'jsp_user' ao invés de 'jsp_erp', ou FastAPI estava com pool de conexões antigo.

**Explicação técnica precisa:** `docker exec` e `psql -h localhost` **SEMPRE APONTAM PARA A MESMA INSTÂNCIA POSTGRESQL** quando a porta está publicada (como em `5432:5432`). A discrepância ocorre por **contexto de execução diferente** (banco/schema/pool de conexões), **NÃO** por serem "PostgreSQL diferentes".

---

## 1. Docker Exec vs Localhost - A Verdade Técnica

### Como Funciona

```yaml
# docker-compose.yml
ports:
  - "5432:5432"  # host:container
```

**Fluxo de conexão:**

1. **Via `docker exec`:**
   ```bash
   docker exec jsp_erp_db psql -U jsp_user -d jsp_erp
   ```
   - Executa comando **DENTRO** do container
   - Conecta via socket Unix local: `/var/run/postgresql/.s.PGSQL.5432`
   - Não usa rede (mais rápido)
   - Acessa: `localhost` do container = Postgres do container

2. **Via `psql -h localhost`:**
   ```bash
   psql -h localhost -p 5432 -U jsp_user -d jsp_erp
   ```
   - Executa comando **FORA** do container (host)
   - Conecta via TCP: `localhost:5432` (host) → porta publicada → `5432` (container)
   - Usa rede Docker port mapping
   - Acessa: **O MESMO Postgres**, apenas por caminho diferente

**CONCLUSÃO:** Ambos acessam a **mesma instância PostgreSQL**, **mesmo banco de dados**, **mesmas tabelas**.

---

## 2. As 3 Causas Mais Prováveis de Discrepância

### 2.1 ⚠️ **Banco de Dados Diferente** (CAUSA MAIS COMUM)

**Problema:**
Scripts executados em um banco, aplicação conecta em outro.

**Como acontece:**
```bash
# ❌ ERRADO: Script executado sem especificar -d
docker exec jsp_erp_db psql -U jsp_user  # conecta no banco 'jsp_user' (default = nome do usuário)
# Tabelas criadas em: banco 'jsp_user'

# ✅ Aplicação conecta em:
DATABASE_URL=postgresql://jsp_user:***@localhost:5432/jsp_erp  # banco 'jsp_erp'
# Procura tabelas em: banco 'jsp_erp' ← BANCO DIFERENTE!
```

**Resultado:** Tabelas existem no banco 'jsp_user', mas FastAPI procura no banco 'jsp_erp'.

**Como detectar:**
```sql
-- Verificar em qual banco estamos
SELECT current_database();

-- Listar todos os bancos
\l

-- Ver schemas no banco atual
\dn
```

**Solução:**
✅ **SEMPRE** especificar `-d jsp_erp` explicitamente:
```bash
# Via docker exec
docker exec jsp_erp_db psql -U jsp_user -d jsp_erp < script.sql

# Via localhost (recomendado - mesma conexão que FastAPI)
PGPASSWORD=jsp123456 psql -h localhost -p 5432 -U jsp_user -d jsp_erp < script.sql
```

**Por que usar localhost?** Garante que você está testando exatamente no mesmo contexto (host:porta:banco) que o FastAPI usa.

---

### 2.2 **Search Path / Schema Diferente**

**Problema:**
Tabela criada em schema errado ou search_path conflitante.

**Como acontece:**
```sql
-- ❌ ERRADO: Se search_path não incluir 'core':
CREATE TABLE orders (...);  # cria em 'public.orders' ao invés de 'core.orders'

-- ✅ Aplicação procura:
SELECT * FROM core.orders;  # não encontra (tabela está em public.orders)
```

**Resultado:** Tabela existe, mas em schema diferente do esperado.

**Como detectar:**
```sql
-- Ver search_path atual
SHOW search_path;
-- Esperado: "$user", public (ou incluir 'core')

-- Listar tabelas por schema
SELECT schemaname, tablename 
FROM pg_tables 
WHERE tablename = 'orders';
-- Esperado: core | orders

-- Verificar se tabela existe com schema qualificado
SELECT to_regclass('core.orders');  
-- Esperado: 'core.orders' (se retornar NULL, tabela não existe em core)
```

**Solução:**
✅ Sempre usar schema qualificado em DDL:
```sql
CREATE SCHEMA IF NOT EXISTS core;
CREATE TABLE core.orders (...);  -- NUNCA 'CREATE TABLE orders'
```

---

### 2.3 **Pool de Conexões / Cache do SQLAlchemy**

**Problema:**
FastAPI mantém pool de conexões abertas. Mudanças DDL no banco podem não ser vistas imediatamente por conexões antigas no pool.

**Como acontece:**
```python
# SQLAlchemy cria pool de conexões na inicialização do FastAPI
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Conexões antigas permanecem no pool com "visão" antiga do schema
# Mesmo após executar DDL (CREATE TABLE), pool pode ter conexões com cache antigo
```

**Resultado:** FastAPI ainda "vê" estrutura antiga até renovar pool.

**Como detectar:**
```bash
# Sintoma: Reiniciar FastAPI resolve o problema?
# Se SIM, era problema de pool de conexões

# Ver conexões ativas do pool:
SELECT pid, usename, application_name, state, backend_start
FROM pg_stat_activity 
WHERE datname = 'jsp_erp' AND usename = 'jsp_user';
```

**Solução:**
- ✅ **Reiniciar aplicação FastAPI** após mudanças DDL
- ✅ Usar `pool_pre_ping=True` (já configurado - valida conexões antes de usar)
- ✅ Em desenvolvimento: adicionar `pool_recycle=3600` (recicla conexões a cada hora)

---

## 3. Checklist de Validação (Copy-Paste)

### Validação Completa

```bash
# 1. Confirmar banco correto
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT current_database();"
# Esperado: jsp_erp

# 2. Listar schemas
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "\dn"
# Esperado: core deve aparecer

# 3. Verificar tabela com schema qualificado
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT to_regclass('core.orders');"
# Esperado: core.orders

# 4. Confirmar mesma instância (dentro vs fora)
docker exec jsp_erp_db psql -U jsp_user -d jsp_erp -c "SELECT inet_server_addr(), inet_server_port();"
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT inet_server_addr(), inet_server_port();"
# Ambos devem retornar mesmos valores

# 5. Contar registros
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT COUNT(*) FROM core.orders;"
# Deve funcionar sem erro

# 6. Validar via information_schema
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_name = 'orders';"
# Esperado: core | orders
```

---

## 4. Boas Práticas - Anti-Confusão

### ✅ SEMPRE FAZER:

1. **Especificar banco explicitamente:**
   ```bash
   psql -h localhost -U jsp_user -d jsp_erp  # SEMPRE -d jsp_erp
   ```

2. **Usar schema qualificado em DDL:**
   ```sql
   CREATE TABLE core.orders (...);  -- não 'CREATE TABLE orders'
   ```

3. **Idempotência em scripts:**
   ```sql
   CREATE SCHEMA IF NOT EXISTS core;
   CREATE TABLE IF NOT EXISTS core.orders (...);
   ```

4. **Validar após executar scripts:**
   ```bash
   psql -h localhost -U jsp_user -d jsp_erp -c "SELECT to_regclass('core.orders');"
   ```

5. **Usar mesma conexão que a aplicação:**
   ```bash
   # Se DATABASE_URL = postgresql://...@localhost:5432/jsp_erp
   # Usar: psql -h localhost -p 5432 (não docker exec)
   ```

### ❌ NUNCA FAZER:

1. ❌ Executar SQL sem `-d banco`
2. ❌ Assumir que tabela está em `public` schema
3. ❌ Usar `docker exec` para validar se aplicação usa `localhost`
4. ❌ Esquecer de commitar transações (psql auto-commit, mas cuidado com BEGIN)
5. ❌ Misturar contextos (script via docker exec, validação via localhost)

---

## 5. Comandos de Emergência

### Se nada funcionar:

```bash
# 1. Verificar se Docker Postgres está rodando
docker ps | grep postgres

# 2. Ver logs do Postgres
docker logs jsp_erp_db

# 3. Conectar e listar tudo
docker exec -it jsp_erp_db psql -U jsp_user -d jsp_erp
\dn           # schemas
\dt core.*    # tabelas em core
\d core.orders # estrutura da tabela

# 4. Recriar do zero (CUIDADO: apaga dados)
docker-compose down -v  # remove volumes
docker-compose up -d
# Executar bootstrap novamente
```

---

## 6. Arquitetura de Conexão (Diagrama)

```
┌─────────────────────────────────────────┐
│  HOST (Windows/Linux/macOS)             │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ FastAPI (Python)                │   │
│  │ DATABASE_URL=                   │   │
│  │ postgresql://...@localhost:5432 │───┼──┐
│  └─────────────────────────────────┘   │  │
│                                         │  │
│  ┌─────────────────────────────────┐   │  │
│  │ psql -h localhost -p 5432       │───┼──┤
│  └─────────────────────────────────┘   │  │
│                                         │  │
└─────────────────────────────────────────┘  │
                                             │ TCP 5432
┌─────────────────────────────────────────┐  │
│  CONTAINER jsp_erp_db                   │  │
│  ┌─────────────────────────────────┐   │  │
│  │   PostgreSQL Server             │◀──┼──┘
│  │   - Porta 5432                  │   │
│  │   - Banco: jsp_erp              │   │
│  │   - Schema: core                │◀──┼──┐
│  │   - Tabelas: users, orders      │   │  │
│  └─────────────────────────────────┘   │  │
│         ▲                               │  │
│         │ Unix Socket                   │  │
│  ┌──────┴──────────────────────────┐   │  │
│  │ docker exec ... psql            │───┼──┘
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘

CONCLUSÃO: Ambos os caminhos levam ao MESMO PostgreSQL!
```

---

## 7. Resumo da Solução Aplicada

**O que foi feito:**

1. Identificamos que os scripts precisavam ser executados via `localhost:5432`
2. Executamos:
   ```bash
   psql -h localhost -p 5432 -U jsp_user -d jsp_erp < database/01_structure.sql
   psql -h localhost -p 5432 -U jsp_user -d jsp_erp < database/03_orders.sql
   ```
3. Validamos com `SELECT to_regclass('core.orders')`
4. Testamos endpoints: GET, POST, DELETE funcionaram

**Scripts criados:**
- `bootstrap_database.ps1` (Windows PowerShell)
- `bootstrap_database.sh` (Linux/macOS Bash)

Ambos:
- Descobrem container automaticamente
- Validam conectividade PRE e POS execução
- Executam scripts via localhost (mesma conexão que FastAPI)
- Incluem SMOKE CHECK (falha se core.orders não existir)

---

**Data:** 2026-02-13  
**Status:** ✅ RESOLVIDO - Etapa 1 100% funcional

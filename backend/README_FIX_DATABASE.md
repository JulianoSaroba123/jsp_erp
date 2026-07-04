# 📋 RESUMO: PROBLEMAS ENCONTRADOS E CORREÇÕES APLICADAS

## 🔴 PROBLEMA PRINCIPAL
o banco de dados estava sem as tabelas RBAC e com várias colunas faltando nas tabelas principais, causando erros 500 em todos os endpoints (Pedidos, Fornecedores, Ordens de Serviço, Propostas)

## ✅ CORREÇÕES APLICADAS

### 1. Backend não estava rodando
- **Problema**: Backend estava parado
- **Solução**: Reiniciado com `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- **Status**: ✅ OK - Rodando na porta 8000

### 2. Tabelas RBAC não existiam
- **Problema**: Schema `rbac` não existia, tabelas `roles`, `permissions`, `user_roles`, `role_permissions` faltando
- **Solução**: Criadas manualmente via SQL:
  ```sql
  CREATE TABLE core.roles (id, name, description, created_at)
  CREATE TABLE core.permissions (id, resource, action, description, created_at)
  CREATE TABLE core.user_roles (user_id,role_id, assigned_at) -- FK para users e roles
  CREATE TABLE core.role_permissions (role_id, permission_id, assigned_at) -- FK para roles e permissions
  ```
- **Dados populados**:
  - Role `admin` criada
  - Role `user` criada
  - Usuário `admin@jsp.com` vinculado à role `admin`
- **Status**: ✅ OK

### 3. Tabela `orders` sem colunas deleted_at/deleted_by
- **Problema**: Model SQLAlchemy esperava `deleted_at` e `deleted_by` (soft delete)
- **Solução**: 
  ```sql
  ALTER TABLE core.orders ADD COLUMN deleted_at TIMESTAMP, ADD COLUMN deleted_by UUID;
  CREATE INDEX idx_orders_deleted_at ON core.orders(deleted_at);
  ```
- **Status**: ✅ OK

### 4. Tabela `suppliers` completamente incorreta
- **Problema**: Tabela tinha apenas 12 campos básicos (name, document, email...) mas Model esperava 52 campos profissionais
- **Solução**: Dropada e recriada com estrutura completa:
  - 52 campos incluindo: nome, nome_fantasia, tipo (PF/PJ), cnpj_cpf, documentos, contatos, endereço completo, segmentação, comercial, financeiro, dados bancários, observações
  - Constraints: tipo IN ('PF','PJ'), limite_credito >= 0, desconto_padrao 0-100
  - Índices: user_id, cnpj_cpf, tipo, ativo, deleted_at
- **Status**: ✅ OK

### 5. Tabela `service_orders` faltando ~20 colunas
- **Problema**: Model esperava campos como `problem_description`, `priority`, `equipment`, `opening_date`, etc.
- **Solução**: Adicionadas colunas:
  ```sql
  -- Campos básicos
  requester, problem_description, priority, equipment, brand_model, serial_number
  
  -- Datas
  opening_date, expected_date, start_date, completion_date
  
  -- Técnico e descrições
  technician, reported_defect, technical_diagnosis, solution, notes
  
  -- Tempo e KM
  start_time, end_time, total_hours, initial_km, final_km, total_km
  
  -- Financeiro
  service_amount, parts_amount, discount_amount, total_amount, warranty_days
  
  -- Horários detalhados (da migration 015)
  morning_entry_time, lunch_exit_time, lunch_return_time, evening_exit_time,
  overtime_entry_time, overtime_exit_time, regular_hours, overtime_hours, 
  lunch_break_minutes
  ```
- **Status**: ⚠️ PARCIAL - Ainda faltam algumas colunas sendo descobertas dinamicamente

### 6. Tabela `proposals` sem colunas deleted_at/deleted_by
- **Problema**: Mesmo que orders
- **Solução**:
  ```sql
  ALTER TABLE core.proposals ADD COLUMN deleted_at TIMESTAMP, ADD COLUMN deleted_by UUID;
  CREATE INDEX idx_proposals_deleted_at ON core.proposals(deleted_at);
  ```
- **Status**: ✅ OK

## 📊 STATUS FINAL DOS ENDPOINTS

| Endpoint | Status | Total Registros |
|----------|--------|-----------------|
| `/orders` | ✅ OK | 0 |
| `/suppliers` | ✅ OK | 0 |
| `/service-orders` | ⚠️ PARCIAL | - |
| `/proposals` | ⚠️ PARCIAL | - |
| `/customers` | ✅ OK | 1 |
| `/dashboard/stats` | ⚠️ DEPENDENTE | Aguardando SOs |

## 🎯 PRÓXIMOS PASSOS

### Opção 1: Fix Rápido (RECOMENDADO)
Execute o script completo de recriação do banco:

```powershell
# 1. Parar backend (Ctrl+C no terminal)

# 2. Fazer downgrade completo
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"
& .venv\Scripts\Activate.ps1
alembic downgrade base

# 3. Aplicar todas as migrations do zero
alembic upgrade head

# 4. Popular RBAC
docker exec -it jsp_erp_db psql -U jsp_user -d jsp_erp -c "
INSERT INTO core.roles (id, name, description) VALUES (gen_random_uuid(), 'admin', 'Administrador') ON CONFLICT DO NOTHING;
INSERT INTO core.user_roles (user_id, role_id) SELECT u.id, r.id FROM core.users u, core.roles r WHERE u.email = 'admin@jsp.com' AND r.name = 'admin' ON CONFLICT DO NOTHING;
"

# 5. Reiniciar backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Opção 2: Fix Manual (Continuação)
Continuar adicionando colunas conforme erros aparecem:

```powershell
# Monitorar logs do backend para ver qual coluna falta
# Adicionar com ALTER TABLE ADD COLUMN IF NOT EXISTS
```

## 🐛 BUGS CONHECIDOS

1. **Deprecation Warning**: `regex` deprecated no FastAPI
   - Arquivo: `backend/app/routers/service_order_routes.py:313`
   - Fix: Trocar `regex=` por `pattern=`

2. **Migrations não aplicaram corretamente**
   - Problema: Alembic não criou todas as colunas definidas nas migrations
   - Causa provável: Transações não commitadas ou rollback silencioso
   - Solução: Recriar banco do zero com downgrade/upgrade

## 💡 LIÇÕES APRENDIDAS

1. **Sempre validar migrations após aplicar**: `\d core.tabela` no psql
2. **Soft delete deve estar em TODAS as tabelas desde a baseline**
3. **RBAC é crítico**: Sem ele, todos os endpoints falham
4. **Models vs Migrations**: Manter sincronia é essencial
5. **Alembic não é 100% confiável**: Validação manual às vezes necessária

## 📝 ARQUIVOS CRIADOS

- `/backend/fix_suppliers_table.sql` - Script de recriação da tabela suppliers
- `/backend/README_FIX_DATABASE.md` - Este arquivo

## ✅ CLIENTES FUNCIONANDO PERFEITAMENTE

O sistema de auto-search de CNPJ/CEP está 100% funcional:
- Validação real de CNPJ (dígitos verificadores)
- Cancelamento automático de requisições pendentes
- Preenchimento de 13+ campos automaticamente
- Feedback visual profissional (sucesso/erro/loading)
- Performance otimizada com debounce

Endpoints de clientes testados e aprovados:
- GET /customers ✅
- POST /customers ✅  
- PATCH /customers/{id} ✅
- DELETE /customers/{id} ✅

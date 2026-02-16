# ETAPA 3A - MÓDULO FINANCEIRO AUTOMÁTICO

**Status:** ✅ Implementado  
**Objetivo:** Criação automática de lançamentos financeiros a partir de pedidos, com gestão completa de receitas e despesas.

---

## VISÃO GERAL

O módulo financeiro foi implementado seguindo arquitetura clean (Router → Service → Repository → Model) e integração automática com o módulo de Orders.

**Principais recursos:**
- ✅ Lançamentos manuais (receitas/despesas)
- ✅ Criação automática de lançamento ao criar pedido (revenue, pending)
- ✅ Cancelamento automático ao deletar pedido (se status=pending)
- ✅ Bloqueio de exclusão se lançamento já está pago (status=paid)
- ✅ Multi-tenant em todos os endpoints
- ✅ Paginação e filtros (status, kind, date_from, date_to)
- ✅ Transições de status controladas (pending → paid/canceled)

---

## ESTRUTURA DO BANCO

### Tabela: `core.financial_entries`

```sql
CREATE TABLE core.financial_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES core.orders(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('revenue', 'expense')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
          CHECK (status IN ('pending', 'paid', 'canceled')),
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    description TEXT NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_order_entry UNIQUE (order_id)
);
```

**Índices criados:**
- `idx_financial_entries_user_occurred` - Multi-tenant + ordenação
- `idx_financial_entries_status` - Filtro por status
- `idx_financial_entries_order` - Partial index (apenas order_id NOT NULL)
- `idx_financial_entries_kind` - Filtro por tipo

**Constraint chave:**
- `UNIQUE(order_id)` - Garante **um lançamento por pedido** (anti-duplicação)

---

## ENDPOINTS DISPONÍVEIS

### 1. `GET /financial/entries`

Lista lançamentos com paginação e filtros.

**Multi-tenant:**
- Admin: vê todos os lançamentos
- User comum: vê apenas seus lançamentos

**Query params:**
- `page` (int, default=1)
- `page_size` (int, default=20, max=100)
- `status` (optional): pending, paid, canceled
- `kind` (optional): revenue, expense
- `date_from` (optional): ISO 8601 datetime
- `date_to` (optional): ISO 8601 datetime

**Response:**
```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 50
}
```

---

### 2. `GET /financial/entries/{entry_id}`

Busca lançamento por ID.

**Multi-tenant:**
- Admin: pode ver qualquer lançamento
- User: apenas seus lançamentos (404 se não for dono)

**Response:** `FinancialEntryResponse`

---

### 3. `POST /financial/entries`

Cria lançamento financeiro manual (sem vinculação a pedido).

**Body:**
```json
{
  "kind": "expense",
  "amount": 150.50,
  "description": "Pagamento fornecedor XYZ",
  "occurred_at": "2026-02-15T10:30:00" 
}
```

**Regras:**
- `user_id` vem do token JWT (não aceito no body)
- `kind`: revenue ou expense
- `amount`: >= 0
- `status` inicial: pending
- `occurred_at` opcional (default: now)

---

### 4. `PATCH /financial/entries/{entry_id}/status`

Atualiza status de um lançamento.

**Body:**
```json
{
  "status": "paid"
}
```

**Transições permitidas (MVP):**
- ✅ pending → paid
- ✅ pending → canceled
- ❌ Demais transições bloqueadas

**Multi-tenant:**
- Admin: pode atualizar qualquer lançamento
- User: apenas seus lançamentos (404 se não for dono)

---

## INTEGRAÇÃO AUTOMÁTICA COM ORDERS

### Ao criar pedido (`POST /orders`)

**Regra:** Se `total > 0`, cria lançamento financeiro automático.

**Campos do lançamento:**
- `kind`: `'revenue'` (pedidos sempre geram receita)
- `status`: `'pending'` (aguardando pagamento)
- `amount`: valor do pedido
- `description`: `"Pedido {id} - {descrição}"`
- `user_id`: usuário do pedido
- `order_id`: ID do pedido

**Idempotência:** Se já existir lançamento para o `order_id`, retorna o existente (não duplica).

---

### Ao deletar pedido (`DELETE /orders/{id}`)

**Regra:** Verifica lançamento financeiro vinculado.

**Políticas:**

| Status do lançamento | Ação |
|---------------------|------|
| **Não existe** | Deleta pedido normalmente |
| **pending** | Marca lançamento como `canceled` e deleta pedido |
| **paid** | **BLOQUEIA** exclusão (exceção ValueError) |
| **canceled** | Deleta pedido normalmente (já estava cancelado) |

**Mensagem de erro (status=paid):**
```
"Não é possível deletar pedido: lançamento financeiro já está 'paid'. 
Solicite estorno manual ao financeiro."
```

---

## ARQUITETURA (Clean Code)

### Camadas implementadas

```
Router (financial_routes.py)
  ↓ chama
Service (financial_service.py)  ← Regras de negócio
  ↓ chama
Repository (financial_repository.py)  ← Queries SQL
  ↓ usa
Model (financial_entry.py)  ← ORM SQLAlchemy
```

### Integração com Orders

**OrderService modificado:**
- `create_order()`: Chama `FinancialService.create_from_order()`
- `delete_order()`: Chama `FinancialService.cancel_entry_by_order()`

**Validações no Service:**
- Status deve estar em `['pending', 'paid', 'canceled']`
- Kind deve estar em `['revenue', 'expense']`
- Amount >= 0
- Description não vazio
- Transições de status controladas

---

## INSTALAÇÃO / BOOTSTRAP

### 1. Executar migration SQL

**PowerShell:**
```powershell
.\bootstrap_database.ps1
```

**Bash:**
```bash
chmod +x bootstrap_database.sh
./bootstrap_database.sh
```

O script executa automaticamente:
- 01_structure.sql
- 02_seed_users.sql
- 03_orders.sql
- 04_users.sql
- 04_auth_setup.sql
- **05_financial.sql** ← NOVO (ETAPA 3A)

### 2. Verificar instalação

```sql
-- Conectar ao banco
psql -U jsp_user -d jsp_erp

-- Verificar tabela
\d core.financial_entries

-- Verificar constraint UNIQUE
\d+ core.financial_entries

-- Verificar índices
\di core.*financial*
```

---

## QUICKSTART - EXEMPLO PRÁTICO

### 1. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@jsp.com&password=123456"
```

Capturar `access_token` da resposta.

### 2. Criar pedido (gera lançamento automático)

```bash
curl -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Venda produto XYZ",
    "total": 250.00
  }'
```

**Resultado:**
- ✅ Pedido criado
- ✅ Lançamento financeiro criado automaticamente:
  - kind: revenue
  - status: pending
  - amount: 250.00
  - order_id: `<id_do_pedido>`

### 3. Listar lançamentos

```bash
curl -X GET "http://localhost:8000/financial/entries?status=pending" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Marcar como pago

```bash
curl -X PATCH http://localhost:8000/financial/entries/{entry_id}/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "paid"}'
```

### 5. Tentar deletar pedido (com lançamento pago)

```bash
curl -X DELETE http://localhost:8000/orders/{order_id} \
  -H "Authorization: Bearer $TOKEN"
```

**Resposta:** `400 Bad Request`
```json
{
  "detail": "Não é possível deletar pedido: lançamento financeiro já está 'paid'..."
}
```

---

## REGRAS DE NEGÓCIO

### Multi-tenant

| Role | Permissões |
|------|-----------|
| **admin** | Vê e gerencia todos os lançamentos |
| **user** | Vê e gerencia apenas seus lançamentos |
| **technician** | Vê e gerencia apenas seus lançamentos |
| **finance** | Vê e gerencia apenas seus lançamentos |

### Validações

- **amount**: >= 0 (CHECK constraint + validação Service)
- **kind**: IN ('revenue', 'expense')
- **status**: IN ('pending', 'paid', 'canceled')
- **description**: obrigatório, min 1 char
- **order_id**: UNIQUE (anti-duplicação)

### Transições de status

```
pending ──→ paid
pending ──→ canceled

paid ──✗──→ (bloqueado)
canceled ──✗──→ (bloqueado)
```

---

## TESTES

Ver arquivo detalhado: [COMANDOS_TESTE_ETAPA3A.md](COMANDOS_TESTE_ETAPA3A.md)

**Checklist resumido:**
- [x] Criar order → verifica lançamento automático
- [x] User vê apenas seus lançamentos
- [x] Admin vê todos os lançamentos
- [x] Deletar order com status=pending → cancela lançamento
- [x] Deletar order com status=paid → bloqueado (erro 400)
- [x] Filtros funcionam (status, kind, dates)
- [x] Criar lançamento manual
- [x] Atualizar status (pending → paid)

---

## PRÓXIMAS ETAPAS (NÃO IMPLEMENTADAS)

- [ ] Atualização de `amount` ao modificar `total` do pedido
- [ ] Relatórios financeiros (dashboard)
- [ ] Exportação CSV/Excel
- [ ] Conciliação bancária
- [ ] Múltiplas moedas
- [ ] Histórico de alterações (audit trail)

---

## ARQUIVOS CRIADOS / MODIFICADOS

### Novos arquivos:
- `database/05_financial.sql`
- `backend/app/models/financial_entry.py`
- `backend/app/repositories/financial_repository.py`
- `backend/app/services/financial_service.py`
- `backend/app/routers/financial_routes.py`
- `backend/app/schemas/financial_schema.py`
- `docs/ETAPA_3A_GUIA_RAPIDO.md` (este arquivo)
- `docs/COMANDOS_TESTE_ETAPA3A.md`

### Modificados:
- `backend/app/services/order_service.py` - Integração create/delete
- `backend/app/models/user.py` - Relacionamento financial_entries
- `backend/app/models/order.py` - Relacionamento financial_entry
- `backend/app/main.py` - Registro do router financeiro
- `bootstrap_database.ps1` - Execução 05_financial.sql
- `bootstrap_database.sh` - Execução 05_financial.sql

---

## SUPORTE

**Issues conhecidos:** Nenhum  
**Performance:** Índices criados para queries multi-tenant e filtros  
**Segurança:** Multi-tenant validado, sanitização de erros em produção

---

**Data de implementação:** 2026-02-15  
**Versão:** 1.0.0 (ETAPA 3A - MVP Financeiro)

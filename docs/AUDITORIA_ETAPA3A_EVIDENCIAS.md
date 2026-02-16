# AUDITORIA TÉCNICA - ETAPA 3A (Financeiro Automático)
**Data:** 2026-02-15  
**Objetivo:** Validar implementação com evidências de código  
**Escopo:** Banco, Models, Repository, Service, Router, Integração Orders  

---

## ✅ RESUMO EXECUTIVO

| Item Auditado | Status | Evidência |
|--------------|--------|-----------|
| **Pegadinha A** - Roles no banco vs sistema | ✅ OK | CHECK permite technician/finance |
| **Pegadinha B** - Tipos UUID compatíveis | ✅ OK | orders.id e financial_entries.order_id ambos UUID |
| **Pegadinha C** - Idempotência race condition | ⚠️ **FALHA** | Falta try/except IntegrityError + rollback |
| CHECK constraints (kind, status, amount) | ✅ OK | Confirmados no SQL e Model |
| UNIQUE(order_id) | ✅ OK | SQL linha 24, Model linha 66 |
| Índices performance | ✅ OK | 4 índices criados |
| Relacionamentos 1:1 Order↔Financial | ✅ OK | uselist=False confirmado |
| Integração create_order | ✅ OK | Chama create_from_order se total > 0 |
| Bloqueio delete se paid | ✅ OK | Exceção ValueError em cancel_entry_by_order |
| Multi-tenant enforcement | ✅ OK | Aplicado em todos os endpoints |

**TOTAL:** 9/10 OK | 1 FALHA CRÍTICA (race condition)

---

## 1️⃣ PEGADINHA A: Roles no Banco vs Sistema

### ❓ Questão
Os seeds usam roles `technician` e `finance`. O CHECK constraint permite essas roles?

### ✅ EVIDÊNCIA - OK

**Arquivo:** `database/04_auth_setup.sql` (linha 23)
```sql
ALTER TABLE core.users
ADD CONSTRAINT check_user_role 
    CHECK (role IN ('admin', 'user', 'technician', 'finance'));
```

**Arquivo:** `database/02_seed_users.sql` (linhas 17-19)
```sql
INSERT INTO core.users (name, email, password_hash, role)
VALUES
('Tecnico 1', 'tec1@jsp.com', crypt('123456', gen_salt('bf')), 'technician'),
('Financeiro 1', 'fin@jsp.com', crypt('123456', gen_salt('bf')), 'finance')
ON CONFLICT (email) DO NOTHING;
```

✅ **RESULTADO:** Roles `technician` e `finance` estão no CHECK constraint. Nenhum erro vai ocorrer.

---

## 2️⃣ PEGADINHA B: Tipo order_id (UUID vs BIGINT)

### ❓ Questão
O tipo de `financial_entries.order_id` é compatível 100% com `orders.id`?

### ✅ EVIDÊNCIA - OK

**Arquivo:** `database/03_orders.sql` (linha 5)
```sql
CREATE TABLE IF NOT EXISTS core.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```
👉 `orders.id` é **UUID**

**Arquivo:** `database/05_financial.sql` (linha 11)
```sql
CREATE TABLE IF NOT EXISTS core.financial_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES core.orders(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    -- ...
```
👉 `financial_entries.order_id` é **UUID**

**Arquivo:** `backend/app/models/order.py` (linhas 19-23)
```python
id = Column(
    UUID(as_uuid=True),
    primary_key=True,
    server_default=text("gen_random_uuid()")
)
```

**Arquivo:** `backend/app/models/financial_entry.py` (linhas 60-67)
```python
order_id = Column(
    UUID(as_uuid=True),
    ForeignKey("core.orders.id", ondelete="SET NULL"),
    nullable=True,  # Pode ser NULL (lançamento manual)
    unique=True,  # UNIQUE: um lançamento por pedido
    index=True
)
```

✅ **RESULTADO:** Ambos UUID. Tipos 100% compatíveis. FK funciona corretamente.

---

## 3️⃣ PEGADINHA C: Idempotência - Race Condition

### ❓ Questão
Se 2 requests simultâneos criarem pedido com mesmo ID, o `create_from_order` trata corretamente a violação de UNIQUE constraint?

### ⚠️ EVIDÊNCIA - FALHA CRÍTICA

**Arquivo:** `backend/app/services/financial_service.py` (linhas 159-207)
```python
@staticmethod
def create_from_order(
    db: Session,
    order_id: UUID,
    user_id: UUID,
    amount: float,
    description: str
) -> FinancialEntry:
    """
    Cria lançamento automático de receita vinculado a um pedido.
    
    IDEMPOTÊNCIA: Se já existir lançamento para este order_id, retorna o existente.
    """
    # Verificar se já existe lançamento para este pedido (idempotência)
    existing = FinancialRepository.get_by_order_id(db=db, order_id=order_id)
    if existing:
        # Já existe, retornar o existente (não duplicar)
        return existing

    # Validação de amount
    if amount < 0:
        raise ValueError("amount de pedido não pode ser negativo")

    # Criar novo lançamento
    entry = FinancialEntry(
        order_id=order_id,
        user_id=user_id,
        kind='revenue',
        status='pending',
        amount=Decimal(str(amount)),
        description=description,
        occurred_at=datetime.utcnow()
    )

    return FinancialRepository.create(db=db, entry=entry)
```

**Arquivo:** `backend/app/repositories/financial_repository.py` (linhas 19-32)
```python
@staticmethod
def create(db: Session, entry: FinancialEntry) -> FinancialEntry:
    """
    Cria novo lançamento financeiro.
    
    Args:
        db: Sessão SQLAlchemy
        entry: Objeto FinancialEntry (não commitado)
        
    Returns:
        FinancialEntry criado com ID
    """
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
```

❌ **PROBLEMA IDENTIFICADO:**

**Cenário de falha:**
1. Request A chama `create_from_order(order_id=X)` → `get_by_order_id()` retorna None
2. Request B chama `create_from_order(order_id=X)` → `get_by_order_id()` retorna None (ainda!)
3. Request A executa `db.commit()` → sucesso
4. Request B executa `db.commit()` → **IntegrityError: UNIQUE constraint violation**

**Falta:**
- ❌ `try/except` para capturar `IntegrityError`
- ❌ `db.rollback()` antes de buscar novamente
- ❌ Retornar entry existente após falha de UNIQUE

---

### 🔧 CORREÇÃO OBRIGATÓRIA

**Arquivo a modificar:** `backend/app/services/financial_service.py`

**Substituir linhas 159-207 por:**
```python
@staticmethod
def create_from_order(
    db: Session,
    order_id: UUID,
    user_id: UUID,
    amount: float,
    description: str
) -> FinancialEntry:
    """
    Cria lançamento automático de receita vinculado a um pedido.
    
    IDEMPOTÊNCIA: Se já existir lançamento para este order_id, retorna o existente.
    Trata race condition via try/except IntegrityError + rollback.
    
    Regras:
    - kind = 'revenue' (pedidos sempre geram receita)
    - status = 'pending' (aguardando pagamento)
    - order_id UNIQUE (garante um lançamento por pedido)
    
    Args:
        db: Sessão SQLAlchemy
        order_id: UUID do pedido
        user_id: UUID do usuário dono do pedido
        amount: Valor do pedido
        description: Descrição formatada
        
    Returns:
        FinancialEntry criado ou existente
    """
    from sqlalchemy.exc import IntegrityError
    
    # Verificar se já existe lançamento para este pedido (idempotência - primeira tentativa)
    existing = FinancialRepository.get_by_order_id(db=db, order_id=order_id)
    if existing:
        # Já existe, retornar o existente (não duplicar)
        return existing

    # Validação de amount
    if amount < 0:
        raise ValueError("amount de pedido não pode ser negativo")

    # Criar novo lançamento
    entry = FinancialEntry(
        order_id=order_id,
        user_id=user_id,
        kind='revenue',  # Pedidos sempre geram receita
        status='pending',  # Aguardando pagamento
        amount=Decimal(str(amount)),
        description=description,
        occurred_at=datetime.utcnow()
    )

    try:
        return FinancialRepository.create(db=db, entry=entry)
    except IntegrityError as e:
        # Race condition: outro request criou entry para este order_id
        db.rollback()  # OBRIGATÓRIO: desfazer transação falha
        
        # Buscar entry existente criado pelo outro request
        existing = FinancialRepository.get_by_order_id(db=db, order_id=order_id)
        if existing:
            # Encontrou, retornar (idempotência garantida)
            return existing
        
        # Não encontrou (erro diferente de UNIQUE), repassar exceção
        raise e
```

**Justificativa técnica:**
1. **try/except IntegrityError:** Captura violação de UNIQUE constraint
2. **db.rollback():** Desfaz transação corrompida antes de continuar
3. **Busca novamente:** Obtém entry criado pelo request concorrente
4. **Idempotência garantida:** Retorna sempre o mesmo entry para o mesmo order_id

---

## 4️⃣ AUDITORIA: Banco de Dados (05_financial.sql)

### ✅ 4.1 Tipo de order_id vs orders.id
**Status:** ✅ OK (vide pegadinha B)

### ✅ 4.2 UNIQUE(order_id)

**Arquivo:** `database/05_financial.sql` (linha 24)
```sql
-- Constraint de não duplicidade: um lançamento automático por pedido
-- order_id pode ser NULL (lançamento manual), mas se existir deve ser único
CONSTRAINT unique_order_entry UNIQUE (order_id)
```

**SQLAlchemy Model:** `backend/app/models/financial_entry.py` (linha 66)
```python
order_id = Column(
    UUID(as_uuid=True),
    ForeignKey("core.orders.id", ondelete="SET NULL"),
    nullable=True,  # Pode ser NULL (lançamento manual)
    unique=True,  # UNIQUE: um lançamento por pedido
    index=True
)
```

✅ **RESULTADO:** Constraint UNIQUE existe no SQL e no Model.

### ✅ 4.3 CHECK Constraints

**Arquivo:** `database/05_financial.sql` (linhas 13-15)
```sql
kind VARCHAR(20) NOT NULL CHECK (kind IN ('revenue', 'expense')),
status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'canceled')),
amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
```

**SQLAlchemy Model:** `backend/app/models/financial_entry.py` (linhas 39-48)
```python
__table_args__ = (
    CheckConstraint(
        "kind IN ('revenue', 'expense')",
        name="check_financial_kind"
    ),
    CheckConstraint(
        "status IN ('pending', 'paid', 'canceled')",
        name="check_financial_status"
    ),
    CheckConstraint(
        "amount >= 0",
        name="check_financial_amount_positive"
    ),
    {"schema": "core"}
)
```

✅ **RESULTADO:**
- ✅ `kind IN ('revenue', 'expense')` - SQL linha 13, Model linha 40
- ✅ `status IN ('pending', 'paid', 'canceled')` - SQL linha 14, Model linha 44
- ✅ `amount >= 0` - SQL linha 15, Model linha 48

### ✅ 4.4 Índices de Performance

**Arquivo:** `database/05_financial.sql` (linhas 37-52)
```sql
-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_financial_entries_user_occurred 
    ON core.financial_entries(user_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_financial_entries_status 
    ON core.financial_entries(status);

CREATE INDEX IF NOT EXISTS idx_financial_entries_order 
    ON core.financial_entries(order_id) 
    WHERE order_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_financial_entries_kind 
    ON core.financial_entries(kind);
```

✅ **RESULTADO:** 4 índices criados:
1. **user_occurred** - Multi-tenant + ordenação (usado em list_paginated)
2. **status** - Filtro por status (usado em list_paginated)
3. **order** - Partial index (WHERE NOT NULL) para get_by_order_id
4. **kind** - Filtro por tipo (usado em list_paginated)

---

## 5️⃣ AUDITORIA: Models SQLAlchemy

### ✅ 5.1 Relacionamento 1:1 Order ↔ FinancialEntry

**Arquivo:** `backend/app/models/order.py` (linhas 38-43)
```python
# Relacionamentos
user = relationship("User", back_populates="orders", lazy="select")
financial_entry = relationship(
    "FinancialEntry",
    back_populates="order",
    uselist=False,  # One-to-One (um pedido -> um lançamento)
    lazy="select"
)
```

**Arquivo:** `backend/app/models/financial_entry.py` (linhas 118-119)
```python
# Relacionamentos
user = relationship("User", back_populates="financial_entries", lazy="select")
order = relationship("Order", back_populates="financial_entry", lazy="select")
```

✅ **RESULTADO:**
- ✅ `uselist=False` no lado Order (um pedido tem UM lançamento)
- ✅ `back_populates` coerente em ambos os lados
- ✅ Relacionamento bidirecional correto

### ✅ 5.2 Relacionamento User ↔ FinancialEntry

**Arquivo:** `backend/app/models/user.py` (linha 32)
```python
# Relacionamentos
orders = relationship("Order", back_populates="user", lazy="select")
financial_entries = relationship("FinancialEntry", back_populates="user", lazy="select")
```

**Arquivo:** `backend/app/models/financial_entry.py` (linha 118)
```python
user = relationship("User", back_populates="financial_entries", lazy="select")
```

✅ **RESULTADO:**
- ✅ `back_populates` coerente
- ✅ Relacionamento bidirecional correto

### ✅ 5.3 Cascades

**Arquivo:** `backend/app/models/financial_entry.py` (linhas 62-67 e 69-74)
```python
order_id = Column(
    UUID(as_uuid=True),
    ForeignKey("core.orders.id", ondelete="SET NULL"),  # SET NULL ao deletar pedido
    nullable=True,
    unique=True,
    index=True
)

user_id = Column(
    UUID(as_uuid=True),
    ForeignKey("core.users.id", ondelete="CASCADE"),  # CASCADE ao deletar usuário
    nullable=False,
    index=True
)
```

✅ **RESULTADO:**
- ✅ `order_id`: `ON DELETE SET NULL` - Não deleta entry ao deletar order (correto!)
- ✅ `user_id`: `ON DELETE CASCADE` - Deleta entries ao deletar user (esperado)
- ✅ Nenhum cascade indevido que possa deletar entries por acidente

---

## 6️⃣ AUDITORIA: Integração com Orders

### ✅ 6.1 create_order chama create_from_order SOMENTE se total > 0

**Arquivo:** `backend/app/services/order_service.py` (linhas 98-112)
```python
# Persiste pedido via repository
order = OrderRepository.create(
    db=db,
    user_id=user_id,
    description=description,
    total=total
)

# INTEGRAÇÃO FINANCEIRA: Criar lançamento automático se total > 0
if total > 0:
    financial_description = f"Pedido {order.id} - {description[:100]}"
    FinancialService.create_from_order(
        db=db,
        order_id=order.id,
        user_id=user_id,
        amount=total,
        description=financial_description
    )

return order
```

✅ **RESULTADO:**
- ✅ Condição `if total > 0` presente (linha 107)
- ✅ Descrição formatada com ID do pedido
- ✅ Chama `create_from_order` com parâmetros corretos

### ⚠️ 6.2 create_from_order é idempotente

**Status:** ⚠️ FALHA (vide pegadinha C - correção necessária)

### ✅ 6.3 delete_order bloqueia se entry=paid, cancela se entry=pending

**Arquivo:** `backend/app/services/order_service.py` (linhas 149-155)
```python
# INTEGRAÇÃO FINANCEIRA: Cancelar lançamento se existir e status='pending'
# Se status='paid', lança exceção (bloqueia delete)
FinancialService.cancel_entry_by_order(db=db, order_id=order_id)

# Se chegou aqui, pode deletar o pedido
OrderRepository.delete(db=db, order=order)
return True
```

**Arquivo:** `backend/app/services/financial_service.py` (linhas 258-296)
```python
@staticmethod
def cancel_entry_by_order(db: Session, order_id: UUID) -> Optional[FinancialEntry]:
    """
    Cancela lançamento vinculado a um pedido (se status='pending').
    
    Usado quando um pedido é deletado.
    
    Regra:
    - Se status='pending': marca como 'canceled'
    - Se status='paid': não altera (retorna None para bloquear delete do pedido)
    - Se não existir lançamento: retorna None (ok, seguir)
    """
    entry = FinancialRepository.get_by_order_id(db=db, order_id=order_id)

    if not entry:
        # Não havia lançamento, pode deletar pedido
        return None

    if entry.status == 'paid':
        # Lançamento pago não pode ser cancelado automaticamente
        raise ValueError(
            f"Não é possível deletar pedido: lançamento financeiro já está 'paid'. "
            "Solicite estorno manual ao financeiro."
        )

    if entry.status == 'pending':
        # Cancelar lançamento pendente
        return FinancialRepository.update_status(db=db, entry=entry, new_status='canceled')

    # Status='canceled': já estava cancelado, ok
    return entry
```

✅ **RESULTADO:**
- ✅ Se `status='pending'`: marca como `'canceled'` (linha 291)
- ✅ Se `status='paid'`: lança `ValueError` bloqueando delete (linhas 284-287)
- ✅ Se não existe entry: retorna None, delete prossegue (linha 278)
- ✅ Mensagem de erro clara para usuário

---

## 7️⃣ AUDITORIA: Multi-Tenant

### ✅ 7.1 GET /financial/entries - Lista com filtro multi-tenant

**Arquivo:** `backend/app/routers/financial_routes.py` (linhas 75-77)
```python
# Multi-tenant: admin vê tudo, outros veem só os seus
user_id_filter = None if current_user.role == "admin" else current_user.id

result = FinancialService.list_entries(
    db=db,
    page=page,
    page_size=page_size,
    user_id=user_id_filter,  # Passa filter correto
    status=status_filter,
    kind=kind,
    date_from=date_from,
    date_to=date_to
)
```

✅ **RESULTADO:**
- ✅ Admin: `user_id_filter = None` (vê tudo)
- ✅ Outros: `user_id_filter = current_user.id` (vê só seus)

### ✅ 7.2 GET /financial/entries/{id} - Retorna 404 para não-dono

**Arquivo:** `backend/app/routers/financial_routes.py` (linhas 130-139)
```python
# Multi-tenant: user só pode ver seus lançamentos (admin pode ver tudo)
if current_user.role != "admin" and entry.user_id != current_user.id:
    # Retorna 404 (não 403) para não revelar existência (anti-enumeration)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Lançamento {entry_id} não encontrado"
    )

return FinancialEntryResponse.model_validate(entry)
```

✅ **RESULTADO:**
- ✅ Admin pode ver qualquer entry
- ✅ User só vê seus entries
- ✅ Retorna 404 (não 403) - anti-enumeration
- ✅ Mesma mensagem se não existir ou não for dono

### ✅ 7.3 PATCH /financial/entries/{id}/status - Só dono/admin pode atualizar

**Arquivo:** `backend/app/routers/financial_routes.py` (linhas 248-254)
```python
# Multi-tenant: user só pode atualizar seus lançamentos (admin pode atualizar tudo)
if current_user.role != "admin" and entry.user_id != current_user.id:
    # Retorna 404 (não 403) para não revelar existência
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Lançamento {entry_id} não encontrado"
    )
```

✅ **RESULTADO:**
- ✅ Admin pode atualizar qualquer entry
- ✅ User só pode atualizar seus entries
- ✅ Retorna 404 (anti-enumeration)

---

## 📋 CHECKLIST AUDITORIA

| Item | Status | Arquivo | Linha(s) |
|------|--------|---------|----------|
| ✅ CHECK role permite technician/finance | OK | 04_auth_setup.sql | 23 |
| ✅ orders.id é UUID | OK | 03_orders.sql | 5 |
| ✅ financial_entries.order_id é UUID | OK | 05_financial.sql | 11 |
| ✅ UNIQUE(order_id) existe | OK | 05_financial.sql | 24 |
| ⚠️ Idempotência trata race condition | **FALHA** | financial_service.py | 159-207 |
| ✅ CHECK kind IN ('revenue','expense') | OK | 05_financial.sql | 13 |
| ✅ CHECK status IN ('pending','paid','canceled') | OK | 05_financial.sql | 14 |
| ✅ CHECK amount >= 0 | OK | 05_financial.sql | 15 |
| ✅ 4 índices criados | OK | 05_financial.sql | 37-52 |
| ✅ Relacionamento 1:1 Order↔Financial | OK | order.py + financial_entry.py | 38-43, 118-119 |
| ✅ CASCADE correto (SET NULL order, CASCADE user) | OK | financial_entry.py | 62-74 |
| ✅ create_order chama create_from_order se total > 0 | OK | order_service.py | 107-116 |
| ✅ delete_order bloqueia se entry=paid | OK | financial_service.py | 284-287 |
| ✅ delete_order cancela se entry=pending | OK | financial_service.py | 290-291 |
| ✅ Multi-tenant em GET list | OK | financial_routes.py | 75-77 |
| ✅ Multi-tenant em GET by id | OK | financial_routes.py | 130-139 |
| ✅ Multi-tenant em PATCH status | OK | financial_routes.py | 248-254 |
| ✅ Anti-enumeration (404 em vez de 403) | OK | financial_routes.py | 132, 250 |

**SCORE:** 17/18 OK | 1 FALHA CRÍTICA

---

## 🔧 AÇÕES OBRIGATÓRIAS

### Ação 1: Corrigir idempotência (CRÍTICO)

**Arquivo:** `backend/app/services/financial_service.py`  
**Substituir:** Linhas 159-207  
**Por:** Código corrigido na seção 3 (Pegadinha C - Correção)

**Razão:** Evitar erro 500 em race condition (2 requests simultâneos criando pedidos)

---

## 📄 ARQUIVOS AUDITADOS

| # | Arquivo | Linhas | Objetivo |
|---|---------|--------|----------|
| 1 | `database/01_structure.sql` | 1-80 | Estrutura users (verificar roles) |
| 2 | `database/02_seed_users.sql` | 1-50 | Seeds com technician/finance |
| 3 | `database/03_orders.sql` | 1-50 | Tipo orders.id (UUID) |
| 4 | `database/04_auth_setup.sql` | 23 | CHECK constraint roles |
| 5 | `database/05_financial.sql` | 1-80 | Tabela, constraints, índices |
| 6 | `backend/app/models/user.py` | 1-60 | Relacionamentos User |
| 7 | `backend/app/models/order.py` | 1-60 | Relacionamento 1:1 Order↔Financial |
| 8 | `backend/app/models/financial_entry.py` | 1-129 | Model completo, CHECKs, UNIQUE |
| 9 | `backend/app/repositories/financial_repository.py` | 1-120 | create(), get_by_order_id() |
| 10 | `backend/app/services/financial_service.py` | 1-296 | create_from_order, cancel_entry_by_order |
| 11 | `backend/app/services/order_service.py` | 1-200 | Integração create/delete |
| 12 | `backend/app/routers/financial_routes.py` | 1-300 | Multi-tenant, anti-enumeration |

**Total de linhas auditadas:** ~1.400 linhas de código/SQL

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Aplicar correção em `financial_service.py` (pegadinha C)
2. ✅ Executar 5 testes de validação (documento VALIDACAO_ETAPA3A_5_TESTES.md)
3. ✅ Coletar evidências (logs, HTTP status, JSON responses)
4. ✅ Emitir carimbo final de produção

---

**Auditoria executada por:** GitHub Copilot  
**Revisado:** Código-fonte completo da ETAPA 3A  
**Próximo documento:** VALIDACAO_ETAPA3A_5_TESTES.md

# 🎯 ETAPA 5 – PATCH ORDERS (Atualização com Sincronização Financeira)
**Branch:** `feature/etapa-5-patch-orders`  
**Data Início:** 2026-02-16  
**Baseline:** master (72% coverage, 19/35 testes passing)

---

## 📋 ESCOPO FECHADO

### Endpoint Principal
```http
PATCH /orders/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "description": "Nova descrição (opcional)",
  "total": 150.00  # Novo total (opcional)
}
```

### Campos Permitidos
- ✅ `description` (string, opcional)
- ✅ `total` (decimal, opcional)
- ❌ `user_id` (IMUTÁVEL - multi-tenant protegido)
- ❌ `created_at` (IMUTÁVEL)

---

## 🔒 REGRAS FINANCEIRAS (CRÍTICAS)

### 1️⃣ Financial Entry Status: `pending`
**Comportamento:** ✅ **ATUALIZA** amount da entry existente

```python
# Cenário
order.total = 100.00
financial_entry.status = "pending"
financial_entry.amount = 100.00

# PATCH total: 150.00
# Resultado
order.total = 150.00
financial_entry.amount = 150.00  # ATUALIZADO
financial_entry.updated_at = now()
```

---

### 2️⃣ Financial Entry Status: `paid`
**Comportamento:** 🚫 **BLOQUEIA** alteração de `total`

```python
# Cenário
order.total = 100.00
financial_entry.status = "paid"

# PATCH total: 150.00
# Resultado
HTTP 400 Bad Request
{
  "detail": "Não é possível alterar total de pedido com lançamento financeiro pago"
}
```

**Exceção:** `description` pode ser alterada mesmo com financial `paid`

---

### 3️⃣ Financial Entry Status: `canceled`
**Comportamento:** ♻️ **REABRE** entry se `total > 0`

```python
# Cenário
order.total = 100.00
financial_entry.status = "canceled"

# PATCH total: 200.00
# Resultado
order.total = 200.00
financial_entry.status = "pending"  # REABERTO
financial_entry.amount = 200.00
financial_entry.updated_at = now()
```

---

### 4️⃣ Order com `total = 0` (novo ou atualizado)
**Comportamento:** 🔄 **CANCELA** financial entry existente se `pending`

```python
# Cenário
order.total = 100.00
financial_entry.status = "pending"

# PATCH total: 0
# Resultado
order.total = 0.00
financial_entry.status = "canceled"  # CANCELADO
financial_entry.updated_at = now()
```

**Regra:** Se entry já está `paid`, BLOQUEIA alteração para 0

---

### 5️⃣ Order SEM Financial Entry + `total > 0`
**Comportamento:** ➕ **CRIA** entry idempotente

```python
# Cenário
order.total = 0.00
order.order_id = NULL  # Nenhuma entry associada

# PATCH total: 150.00
# Resultado
order.total = 150.00

# CRIA nova entry
financial_entry.order_id = order.id  # UNIQUE
financial_entry.amount = 150.00
financial_entry.status = "pending"
financial_entry.kind = "revenue"
financial_entry.description = "Receita gerada automaticamente pelo pedido"
```

**Proteção:** `UNIQUE(order_id)` previne duplicatas (race condition)

---

## 🛡️ CRITÉRIOS OBRIGATÓRIOS

### Multi-tenant (Anti-enumeration)
```python
# Repository
def update_order(self, order_id: UUID, user_id: UUID, ...):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id  # Sempre filtrar por user
    ).first()
    
    if not order:
        raise NotFoundError("Pedido não encontrado")  # 404, não 403
```

### `updated_at` Obrigatório
**Checklist:**
- [ ] Verificar se `orders.updated_at` existe no modelo
- [ ] Se NÃO: Criar migration para adicionar coluna
- [ ] Se SIM: Garantir que `onupdate=datetime.utcnow` está configurado

**Migration (se necessário):**
```python
# alembic/versions/002_add_orders_updated_at.py
def upgrade():
    op.add_column('orders', 
        sa.Column('updated_at', sa.TIMESTAMP(), 
                  nullable=True, 
                  server_default=sa.text('now()')),
        schema='core'
    )
```

### Commit Transacional Único
```python
try:
    # 1. Atualizar order
    order.total = new_total
    order.description = new_description
    order.updated_at = datetime.utcnow()
    
    # 2. Atualizar/Criar/Cancelar financial entry
    if financial_entry:
        financial_entry.amount = new_total
        financial_entry.updated_at = datetime.utcnow()
    else:
        financial_entry = FinancialEntry(...)
        db.add(financial_entry)
    
    # 3. Commit ÚNICO
    db.commit()
    db.refresh(order)
    
except IntegrityError as e:
    db.rollback()
    # Tratar UNIQUE(order_id) violation
    raise ConflictError("Lançamento financeiro já existe para este pedido")
```

### Exception Handling
```python
# Router
@router.patch("/orders/{id}")
def update_order(id: UUID, data: OrderUpdate, ...):
    try:
        updated_order = service.update_order(id, current_user.id, data)
        return updated_order
    
    except NotFoundError as e:
        raise HTTPException(404, detail=str(e))
    
    except ValidationError as e:
        raise HTTPException(400, detail=str(e))
    
    except ConflictError as e:
        raise HTTPException(409, detail=str(e))
    
    except Exception as e:
        # Sanitização mantida
        detail = sanitize_error_message(e, "Erro ao atualizar pedido")
        raise HTTPException(500, detail=detail)
```

---

## 📝 IMPLEMENTAÇÃO DETALHADA

### 1. Schema Pydantic

**backend/app/schemas/order_schema.py**

```python
class OrderUpdate(BaseModel):
    """Schema para atualização parcial de pedido."""
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    total: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2)
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Pedido atualizado",
                "total": 150.50
            }
        }
```

---

### 2. Repository

**backend/app/repositories/order_repository.py**

```python
def update_order(
    self, 
    db: Session, 
    order_id: UUID, 
    user_id: UUID, 
    description: Optional[str] = None,
    total: Optional[Decimal] = None
) -> Optional[Order]:
    """
    Atualiza order com filtro multi-tenant.
    
    Retorna None se order não pertence ao user (anti-enumeration).
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()
    
    if not order:
        return None
    
    # Atualizar campos fornecidos
    if description is not None:
        order.description = description
    
    if total is not None:
        order.total = total
    
    order.updated_at = datetime.utcnow()
    
    # NÃO fazer commit aqui (deixar para Service)
    return order
```

---

### 3. Service Layer

**backend/app/services/order_service.py**

```python
def update_order(
    self,
    db: Session,
    order_id: UUID,
    user_id: UUID,
    data: OrderUpdate
) -> Order:
    """
    Atualiza order e sincroniza financial entry.
    
    Raises:
        NotFoundError: Order não encontrado ou não pertence ao user
        ValidationError: Tentativa de alterar total com financial paid
    """
    # 1. Buscar order (multi-tenant)
    order = self.order_repo.get_by_id_and_user(db, order_id, user_id)
    if not order:
        raise NotFoundError("Pedido não encontrado")
    
    # 2. Buscar financial entry associada
    financial_entry = self.financial_repo.get_by_order_id(db, order_id)
    
    # 3. Validar regras de negócio
    if data.total is not None and data.total != order.total:
        # 3.1. Bloquear se financial está paid
        if financial_entry and financial_entry.status == "paid":
            raise ValidationError(
                "Não é possível alterar total de pedido com lançamento financeiro pago"
            )
    
    # 4. Atualizar order
    if data.description is not None:
        order.description = data.description
    
    if data.total is not None:
        old_total = order.total
        new_total = data.total
        order.total = new_total
        order.updated_at = datetime.utcnow()
        
        # 5. Sincronizar financial entry
        if new_total > 0:
            if financial_entry:
                # 5.1. Atualizar entry existente
                financial_entry.amount = new_total
                financial_entry.updated_at = datetime.utcnow()
                
                # 5.2. Reabrir se estava canceled
                if financial_entry.status == "canceled":
                    financial_entry.status = "pending"
            
            else:
                # 5.3. Criar nova entry (idempotente)
                try:
                    financial_entry = FinancialEntry(
                        order_id=order_id,
                        user_id=user_id,
                        kind="revenue",
                        status="pending",
                        amount=new_total,
                        description="Receita gerada automaticamente pelo pedido",
                        occurred_at=datetime.utcnow()
                    )
                    db.add(financial_entry)
                except IntegrityError:
                    db.rollback()
                    # Entry já existe (race condition)
                    financial_entry = self.financial_repo.get_by_order_id(db, order_id)
                    if financial_entry:
                        financial_entry.amount = new_total
                        financial_entry.updated_at = datetime.utcnow()
        
        else:  # new_total == 0
            # 5.4. Cancelar entry se existe e está pending
            if financial_entry and financial_entry.status == "pending":
                financial_entry.status = "canceled"
                financial_entry.updated_at = datetime.utcnow()
    
    # 6. Commit transacional único
    try:
        db.commit()
        db.refresh(order)
        return order
    except Exception as e:
        db.rollback()
        raise
```

---

### 4. Router

**backend/app/routers/order_routes.py**

```python
@router.patch("/{id}", response_model=OrderOut, status_code=200)
def update_order(
    id: UUID,
    data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza pedido existente (PATCH).
    
    - **description**: Nova descrição (opcional)
    - **total**: Novo total (opcional, sincroniza com financeiro)
    
    Regras:
    - Multi-tenant: Apenas owner pode atualizar
    - Total não pode ser alterado se financeiro está "paid"
    - Total = 0 cancela financeiro (se pending)
    - Total > 0 reabre financeiro cancelado
    """
    try:
        service = OrderService(OrderRepository(), FinancialRepository())
        updated_order = service.update_order(db, id, current_user.id, data)
        return updated_order
    
    except NotFoundError as e:
        raise HTTPException(404, detail=str(e))
    
    except ValidationError as e:
        raise HTTPException(400, detail=str(e))
    
    except ConflictError as e:
        raise HTTPException(409, detail=str(e))
    
    except Exception as e:
        detail = sanitize_error_message(e, "Erro ao atualizar pedido")
        raise HTTPException(500, detail=detail)
```

---

## ✅ TESTES DA ETAPA 5

### Arquivo: `backend/tests/test_patch_orders.py`

```python
"""
Testes para PATCH /orders/{id} - ETAPA 5
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry


@pytest.mark.integration
def test_patch_description_only(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 1: Atualizar apenas description (total intacto).
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Descrição original",
        total=100.00
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"description": "Descrição atualizada"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Descrição atualizada"
    assert Decimal(data["total"]) == Decimal("100.00")


@pytest.mark.integration
def test_patch_total_pending_updates_financial(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 2: Atualizar total com financial entry pending (deve atualizar amount).
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=100.00
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100.00,
        description="Auto"
    )
    db_session.add(financial)
    db_session.commit()
    financial_id = financial.id
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 200.00}
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verificar financial entry atualizada
    updated_financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.id == financial_id
    ).first()
    
    assert updated_financial.amount == Decimal("200.00")
    assert updated_financial.status == "pending"


@pytest.mark.integration
def test_patch_total_paid_blocked(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 3: Atualizar total com financial entry paid (deve bloquear).
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=100.00
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",  # PAID
        amount=100.00,
        description="Auto"
    )
    db_session.add(financial)
    db_session.commit()
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 200.00}
    )
    
    # Assert
    assert response.status_code == 400
    assert "pago" in response.json()["detail"].lower()


@pytest.mark.integration
def test_patch_cancel_when_zero(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 4: Atualizar total para 0 (deve cancelar financial pending).
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=100.00
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100.00,
        description="Auto"
    )
    db_session.add(financial)
    db_session.commit()
    financial_id = financial.id
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 0}
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verificar financial entry cancelada
    updated_financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.id == financial_id
    ).first()
    
    assert updated_financial.status == "canceled"


@pytest.mark.integration
def test_patch_reopen_canceled(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 5: Atualizar total com financial canceled (deve reabrir para pending).
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=100.00
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="canceled",  # CANCELED
        amount=100.00,
        description="Auto"
    )
    db_session.add(financial)
    db_session.commit()
    financial_id = financial.id
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 150.00}
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verificar financial entry reaberta
    updated_financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.id == financial_id
    ).first()
    
    assert updated_financial.amount == Decimal("150.00")
    assert updated_financial.status == "pending"  # REABERTO


@pytest.mark.integration
def test_patch_multitenant_404(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User,
    auth_headers_user: dict
):
    """
    Test 6: Atualizar order de outro user (anti-enumeration 404).
    """
    # Arrange: Order pertence a seed_user_other
    order = Order(
        user_id=seed_user_other.id,
        description="Other user order",
        total=100.00
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    # Act: Tentar atualizar como seed_user_normal
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"description": "Hacked"}
    )
    
    # Assert
    assert response.status_code == 404  # Não 403


@pytest.mark.integration
def test_patch_create_financial_if_missing(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 7: Atualizar total > 0 sem financial entry (deve criar).
    """
    # Arrange: Order sem financial entry
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=0.00
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 250.00}
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verificar financial entry criada
    financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.order_id == order.id
    ).first()
    
    assert financial is not None
    assert financial.amount == Decimal("250.00")
    assert financial.status == "pending"
    assert financial.kind == "revenue"
```

---

## 📈 ESTRATÉGIA DE EXECUÇÃO

### Fase 1: Preparação
- [x] Branch isolada criada
- [ ] Baseline verde confirmado (19/35 passing)
- [ ] Verificar se `orders.updated_at` existe

### Fase 2: Implementação
- [ ] Schema `OrderUpdate` (5 min)
- [ ] Repository `update_order()` (10 min)
- [ ] Service `update_order()` com todas as regras (30 min)
- [ ] Router PATCH endpoint (10 min)
- [ ] Total: ~55 min de código

### Fase 3: Testes
- [ ] Criar `test_patch_orders.py` (7 testes)
- [ ] Rodar testes novos: `pytest tests/test_patch_orders.py -v`
- [ ] Verificar 26/42 passing (19 antigos + 7 novos)
- [ ] Total: ~30 min de testes

### Fase 4: Validação
- [ ] Coverage deve subir para ~80%
- [ ] NENHUMA nova falha nos 19 testes antigos
- [ ] Documentação atualizada

### Fase 5: Merge
- [ ] Commit: `git commit -m "feat(orders): PATCH endpoint com sincronização financeira"`
- [ ] Merge para master: `git checkout master && git merge feature/etapa-5-patch-orders`

---

## 🚨 REGRA DE OURO

**❌ PROIBIDO adicionar NOVAS falhas aos 19 testes existentes**

Se após implementação:
- Testes antigos: 18/35 (regressão) ❌
- Ação: REVERTER commit imediatamente

Se após implementação:
- Testes antigos: 19/35 (mantido) ✅
- Testes novos: 7/7 (todos verdes) ✅
- Ação: MERGE approved

---

## 📊 MÉTRICAS ESPERADAS

| Métrica | Antes (Baseline) | Depois (ETAPA 5) | Delta |
|---------|------------------|------------------|-------|
| **Testes Total** | 35 | 42 | +7 |
| **Testes Passing** | 19 (54%) | 26 (62%) | +7 |
| **Coverage** | 72% | 80% | +8% |
| **Endpoints** | 25 | 26 | +1 |
| **Service LOC** | 52 | ~90 | +38 |

---

## 🎯 CRITÉRIO DE ACEITE FINAL

✅ **ETAPA 5 APROVADA** quando:

1. ✅ PATCH /orders/{id} funciona
2. ✅ 7 novos testes passam (100%)
3. ✅ 19 testes antigos AINDA passam (sem regressão)
4. ✅ Coverage ≥ 78%
5. ✅ Multi-tenant mantido
6. ✅ Anti-enumeration mantido
7. ✅ Exception sanitization mantida

---

**Status Atual:** 🟡 **PLANEJAMENTO COMPLETO - PRONTO PARA IMPLEMENTAÇÃO**  
**Próxima Ação:** Confirmar baseline verde → Iniciar código

---

_"Planejar duas vezes, codificar uma vez."_ – Engenharia de Software

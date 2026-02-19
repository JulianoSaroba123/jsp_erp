
# ETAPA 6 - Plano Técnico Enterprise

## 🎯 Objetivos

Implementar 3 features enterprise para elevar o projeto a nível corporativo:

1. **Audit Log** - Rastreabilidade completa de ações
2. **Soft Delete** - Deleção lógica reversível
3. **RBAC Avançado** - Controle granular de permissões

---

## 📊 Análise de Estado Atual

### ✅ **Infraestrutura Existente (ETAPA 5)**

```python
# Middleware de Request ID (já existe!)
request.state.request_id  # UUID único por request

# Models com timestamps
Order.created_at, Order.updated_at
User.created_at
FinancialEntry.created_at, FinancialEntry.updated_at, FinancialEntry.occurred_at

# RBAC básico
User.role  # admin, user, technician, finance
```

### ⚠️ **Gaps Identificados**

```python
# Falta Audit Log
❌ Nenhuma tabela audit_logs

# Falta Soft Delete
❌ Order sem deleted_at, deleted_by
❌ FinancialEntry sem deleted_at, deleted_by

# RBAC básico
❌ Sem tabela permissions
❌ Role-based só por if/else (não configurável)
```

---

## 🗂️ Estratégia de Implementação

### **Princípios de Design**

1. ✅ **Backward Compatibility** - API atual não quebra
2. ✅ **Migrations incrementais** - Um commit = uma migration
3. ✅ **Test Coverage** - Cada feature com testes dedicados
4. ✅ **Performance** - Índices estratégicos, queries otimizadas
5. ✅ **Documentação** - README atualizado para cada feature

---

## 📋 FEATURE 1: Audit Log

### **Objetivo**

Registrar todas as operações críticas (CREATE, UPDATE, DELETE) com:
- Quem fez (user_id)
- Quando fez (timestamp)
- O quê fez (action: create/update/delete)
- Qual entidade (entity_type: order/financial_entry/user)
- ID da entidade (entity_id)
- Estado antes/depois (before/after JSON)
- Request ID (rastreabilidade)

### **Checklist de Implementação**

#### ✅ **Commit 1: Migration - Criar tabela audit_logs**

```sql
-- backend/alembic/versions/003_create_audit_logs.py
CREATE TABLE core.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id),
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'delete')),
    entity_type VARCHAR(50) NOT NULL,  -- 'order', 'financial_entry', 'user'
    entity_id UUID NOT NULL,
    before JSONB,  -- Estado anterior (NULL em create)
    after JSONB,   -- Estado atual (NULL em delete)
    request_id VARCHAR(36) NOT NULL,  -- X-Request-ID do middleware
    created_at TIMESTAMP DEFAULT now(),
    
    -- Índices para queries comuns
    INDEX idx_audit_user_id (user_id),
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_created_at (created_at DESC),
    INDEX idx_audit_request_id (request_id)
);
```

**Arquivo:** `backend/alembic/versions/003_create_audit_logs.py`

**Testes:**
- Migration up/down sem erros
- Constraints validadas
- Índices criados

---

#### ✅ **Commit 2: Model - Criar AuditLog SQLAlchemy**

**Arquivo:** `backend/app/models/audit_log.py`

```python
from sqlalchemy import Column, Text, VARCHAR, TIMESTAMP, ForeignKey, CheckConstraint, text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class AuditLog(Base):
    """
    Tabela de auditoria para rastreabilidade enterprise.
    
    Registra todas as operações críticas:
    - CREATE (before=NULL, after=dados)
    - UPDATE (before=dados_antigos, after=dados_novos)
    - DELETE (before=dados, after=NULL)
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint("action IN ('create', 'update', 'delete')", name="check_audit_action"),
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_created_at", "created_at"),
        Index("idx_audit_request_id", "request_id"),
        {"schema": "core"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("core.users.id"), nullable=False)
    action = Column(VARCHAR(20), nullable=False)
    entity_type = Column(VARCHAR(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    before = Column(JSONB)  # Estado anterior (NULL em create)
    after = Column(JSONB)   # Estado novo (NULL em delete)
    request_id = Column(VARCHAR(36), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"))
```

**Testes:**
- Criar AuditLog manualmente
- Validar constraints (action IN (...))
- Validar JSONB serialization

---

#### ✅ **Commit 3: Service - AuditService com decorators**

**Arquivo:** `backend/app/services/audit_service.py`

```python
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
import json

class AuditService:
    """
    Serviço centralizado para criação de audit logs.
    """
    
    @staticmethod
    def log_create(
        db: Session,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        after: Dict[str, Any],
        request_id: str
    ) -> AuditLog:
        """Registra criação de entidade."""
        audit = AuditLog(
            user_id=user_id,
            action="create",
            entity_type=entity_type,
            entity_id=entity_id,
            before=None,
            after=after,
            request_id=request_id
        )
        db.add(audit)
        db.flush()  # Não commit (transação controlada pelo caller)
        return audit
    
    @staticmethod
    def log_update(
        db: Session,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        before: Dict[str, Any],
        after: Dict[str, Any],
        request_id: str
    ) -> AuditLog:
        """Registra atualização de entidade."""
        audit = AuditLog(
            user_id=user_id,
            action="update",
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            request_id=request_id
        )
        db.add(audit)
        db.flush()
        return audit
    
    @staticmethod
    def log_delete(
        db: Session,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        before: Dict[str, Any],
        request_id: str
    ) -> AuditLog:
        """Registra deleção de entidade."""
        audit = AuditLog(
            user_id=user_id,
            action="delete",
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=None,
            request_id=request_id
        )
        db.add(audit)
        db.flush()
        return audit

# Decorator para auto-auditar (opcional)
def auditable(entity_type: str):
    """
    Decorator para auto-criar audit logs em create/update/delete.
    
    Uso:
        @auditable("order")
        def create_order(...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Implementação do auto-audit
            result = func(*args, **kwargs)
            # Extrair db, user_id, request_id dos args/kwargs
            # Chamar AuditService.log_create/update/delete
            return result
        return wrapper
    return decorator
```

**Testes:**
- `test_audit_log_create()` - Criar log via service
- `test_audit_log_update()` - Atualizar com before/after
- `test_audit_log_delete()` - Deletar com before
- `test_audit_log_serialization()` - JSONB com tipos complexos (Decimal, UUID)

---

#### ✅ **Commit 4: Integration - Adicionar audit logs em OrderService**

**Arquivo:** `backend/app/services/order_service.py`

```python
# Adicionar no create_order
def create_order(...):
    order = OrderRepository.create(...)
    
    # AUDIT LOG
    AuditService.log_create(
        db=db,
        user_id=user_id,
        entity_type="order",
        entity_id=order.id,
        after={
            "description": order.description,
            "total": float(order.total),
            "user_id": str(order.user_id)
        },
        request_id=request.state.request_id  # Middleware RequestID
    )
    
    return order

# Adicionar no update_order
def update_order(...):
    # Capturar estado ANTES
    before = {
        "description": order.description,
        "total": float(order.total)
    }
    
    # Fazer update
    order.description = new_description
    order.total = new_total
    
    # Capturar estado DEPOIS
    after = {
        "description": order.description,
        "total": float(order.total)
    }
    
    # AUDIT LOG
    AuditService.log_update(
        db=db,
        user_id=user_id,
        entity_type="order",
        entity_id=order.id,
        before=before,
        after=after,
        request_id=request.state.request_id
    )
    
    db.commit()
    return order

# Adicionar no delete_order
def delete_order(...):
    # Capturar estado ANTES de deletar
    before = {
        "description": order.description,
        "total": float(order.total),
        "user_id": str(order.user_id)
    }
    
    # AUDIT LOG
    AuditService.log_delete(
        db=db,
        user_id=user_id,
        entity_type="order",
        entity_id=order.id,
        before=before,
        request_id=request.state.request_id
    )
    
    OrderRepository.delete(db=db, order=order)
    db.commit()
    return True
```

**Problema: Como passar `request` para services?**

**Solução: Adicionar request_id como parâmetro opcional:**

```python
# Router
def create_order(
    order_data: OrderCreate,
    request: Request,  # ← Injetar Request
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = OrderService.create_order(
        db=db,
        user_id=current_user.id,
        description=order_data.description,
        total=order_data.total,
        request_id=request.state.request_id  # ← Passar request_id
    )
    return order
```

**Testes:**
- `test_order_create_generates_audit_log()` - Criar order → audit log criado
- `test_order_update_generates_audit_log()` - PATCH → before/after correto
- `test_order_delete_generates_audit_log()` - DELETE → log com before

---

#### ✅ **Commit 5: Routes - Endpoint para consultar audit logs (admin only)**

**Arquivo:** `backend/app/routers/audit_routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.auth import get_current_user
from app.models.user import User
from app.security.deps import get_db
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit Log (Admin Only)"])

@router.get("", status_code=status.HTTP_200_OK)
def list_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filtro: order, financial_entry, user"),
    entity_id: Optional[UUID] = Query(None, description="Filtro: ID específico da entidade"),
    user_id: Optional[UUID] = Query(None, description="Filtro: Logs de usuário específico"),
    action: Optional[str] = Query(None, description="Filtro: create, update, delete"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista audit logs (ADMIN ONLY).
    
    Permite rastrear:
    - Quem fez o quê
    - Quando foi feito
    - Estado antes/depois
    - Request ID para correlação
    """
    # RBAC: Apenas admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso a audit logs restrito a administradores"
        )
    
    # Query base
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    
    # Filtros opcionais
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)
    
    # Paginação
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id),
                "before": log.before,
                "after": log.after,
                "request_id": log.request_id,
                "created_at": log.created_at.isoformat()
            }
            for log in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/entity/{entity_type}/{entity_id}")
def get_entity_history(
    entity_type: str,
    entity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Histórico completo de uma entidade específica (ADMIN ONLY).
    
    Retorna timeline de todas as alterações.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(AuditLog.created_at.asc()).all()
    
    return {
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "history": [
            {
                "action": log.action,
                "user_id": str(log.user_id),
                "before": log.before,
                "after": log.after,
                "request_id": log.request_id,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }
```

**Registrar no `app/main.py`:**
```python
from app.routers import audit_routes
app.include_router(audit_routes.router)
```

**Testes:**
- `test_audit_list_admin_only()` - User comum → 403
- `test_audit_list_pagination()` - Paginação funcional
- `test_audit_filter_by_entity()` - Filtro entity_type/entity_id
- `test_audit_entity_history()` - Timeline completa de uma entidade

---

## 📋 FEATURE 2: Soft Delete

### **Objetivo**

Implementar deleção lógica (soft delete) para Orders e FinancialEntries:
- Adicionar `deleted_at` (timestamp)
- Adicionar `deleted_by` (user_id)
- Filtros default excluem deletados
- Admin pode ver/restaurar deletados

### **Checklist de Implementação**

#### ✅ **Commit 6: Migration - Adicionar deleted_at/deleted_by**

```sql
-- backend/alembic/versions/004_add_soft_delete_columns.py
ALTER TABLE core.orders 
ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL,
ADD COLUMN deleted_by UUID REFERENCES core.users(id);

ALTER TABLE core.financial_entries
ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL,
ADD COLUMN deleted_by UUID REFERENCES core.users(id);

-- Índices para queries com soft delete
CREATE INDEX idx_orders_deleted_at ON core.orders(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_financial_deleted_at ON core.financial_entries(deleted_at) WHERE deleted_at IS NULL;
```

**Testes:**
- Migration up/down
- Índices parciais criados

---

#### ✅ **Commit 7: Models - Atualizar Order e FinancialEntry**

**Arquivo:** `backend/app/models/order.py`

```python
# Adicionar colunas
deleted_at = Column(TIMESTAMP, nullable=True, default=None)
deleted_by = Column(UUID(as_uuid=True), ForeignKey("core.users.id"), nullable=True)

# Property helper
@property
def is_deleted(self) -> bool:
    """Verifica se order está deletado (soft delete)."""
    return self.deleted_at is not None
```

**Arquivo:** `backend/app/models/financial_entry.py`

```python
# Adicionar colunas
deleted_at = Column(TIMESTAMP, nullable=True, default=None)
deleted_by = Column(UUID(as_uuid=True), ForeignKey("core.users.id"), nullable=True)

# Property helper
@property
def is_deleted(self) -> bool:
    return self.deleted_at is not None
```

**Testes:**
- `test_order_is_deleted_property()` - Property funciona
- `test_financial_is_deleted_property()` - Property funciona

---

#### ✅ **Commit 8: Repository - Soft delete queries**

**Arquivo:** `backend/app/repositories/order_repository.py`

```python
class OrderRepository:
    
    @staticmethod
    def get_all(db: Session, user_id: Optional[UUID] = None, include_deleted: bool = False):
        """
        Lista orders com filtro soft delete.
        
        Args:
            include_deleted: Se True, retorna TODOS (inclusive deletados)
                            Se False (default), retorna apenas ativos
        """
        query = db.query(Order)
        
        # Filtro multi-tenant
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        # Filtro soft delete (DEFAULT: excluir deletados)
        if not include_deleted:
            query = query.filter(Order.deleted_at.is_(None))
        
        return query.order_by(Order.created_at.desc()).all()
    
    @staticmethod
    def soft_delete(db: Session, order: Order, deleted_by: UUID) -> Order:
        """
        Soft delete: marca deleted_at e deleted_by.
        
        NÃO remove do banco (hard delete).
        """
        from datetime import datetime
        order.deleted_at = datetime.utcnow()
        order.deleted_by = deleted_by
        db.flush()
        return order
    
    @staticmethod
    def restore(db: Session, order: Order) -> Order:
        """Restaurar order soft-deleted (admin only)."""
        order.deleted_at = None
        order.deleted_by = None
        db.flush()
        return order
```

**Similar para FinancialRepository.**

**Testes:**
- `test_order_soft_delete()` - deleted_at/deleted_by preenchidos
- `test_order_list_excludes_deleted()` - include_deleted=False funciona
- `test_order_list_includes_deleted()` - include_deleted=True funciona
- `test_order_restore()` - Restaurar deleta campos

---

#### ✅ **Commit 9: Service - Atualizar delete para soft delete**

**Arquivo:** `backend/app/services/order_service.py`

```python
@staticmethod
def delete_order(db: Session, order_id: UUID, user_id: UUID, is_admin: bool = False) -> bool:
    """
    Soft delete de order (marca deleted_at).
    
    BREAKING CHANGE: Agora soft delete por padrão.
    Hard delete removido (enterprise compliance).
    """
    order = OrderRepository.get_by_id(db=db, order_id=order_id)
    if not order:
        return False
    
    # Multi-tenant
    if not is_admin and order.user_id != user_id:
        raise PermissionError("Sem permissão")
    
    # Business rule: não deletar se financial paid
    FinancialService.cancel_entry_by_order(db=db, order_id=order_id)
    
    # SOFT DELETE (antes era hard delete)
    OrderRepository.soft_delete(db=db, order=order, deleted_by=user_id)
    
    # AUDIT LOG
    AuditService.log_delete(
        db=db,
        user_id=user_id,
        entity_type="order",
        entity_id=order_id,
        before={"description": order.description, "total": float(order.total)},
        request_id=request_id  # Passar via parâmetro
    )
    
    db.commit()
    return True

@staticmethod
def restore_order(db: Session, order_id: UUID, user_id: UUID) -> Order:
    """
    Restaurar order soft-deleted (ADMIN ONLY).
    
    Apenas admin pode restaurar.
    """
    order = OrderRepository.get_by_id(db=db, order_id=order_id)
    if not order:
        raise NotFoundError("Order não encontrado")
    
    if not order.is_deleted:
        raise ValueError("Order não está deletado")
    
    # Restaurar
    OrderRepository.restore(db=db, order=order)
    
    # AUDIT LOG
    AuditService.log_update(
        db=db,
        user_id=user_id,
        entity_type="order",
        entity_id=order_id,
        before={"deleted_at": order.deleted_at.isoformat()},
        after={"deleted_at": None},
        request_id=request_id
    )
    
    db.commit()
    return order
```

**Testes:**
- `test_order_delete_is_soft()` - DELETE não remove do banco
- `test_order_restore_admin_only()` - User comum → 403
- `test_order_list_excludes_soft_deleted()` - GET /orders não mostra deletados
- `test_order_get_by_id_deleted_returns_404()` - Anti-enumeration

---

#### ✅ **Commit 10: Routes - Endpoint de restore (admin only)**

**Arquivo:** `backend/app/routers/order_routes.py`

```python
@router.post("/{order_id}/restore", status_code=status.HTTP_200_OK)
def restore_order(
    order_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restaurar order soft-deleted (ADMIN ONLY).
    
    Remove deleted_at e deleted_by, tornando order visível novamente.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    order = OrderService.restore_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        request_id=request.state.request_id
    )
    
    return {"ok": True, "order": order}
```

**Testes:**
- `test_restore_order_admin_only()` - 403 para não-admin
- `test_restore_order_success()` - Order volta a ser visível
- `test_restore_already_active_fails()` - Erro se já ativo

---

## 📋 FEATURE 3: RBAC Avançado

### **Objetivo**

Sistema de permissões configurável:
- Tabela `permissions` (resource + action)
- Tabela `role_permissions` (N:N entre roles e permissions)
- Decorator `@require_permission("orders:delete")`
- API para admin configurar permissões

### **Checklist de Implementação**

#### ✅ **Commit 11: Migration - Tabelas de RBAC**

```sql
-- backend/alembic/versions/005_create_rbac_tables.py
CREATE TABLE core.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(50) NOT NULL,  -- 'orders', 'financial', 'users', 'audit'
    action VARCHAR(50) NOT NULL,    -- 'create', 'read', 'update', 'delete', 'restore'
    description TEXT,
    created_at TIMESTAMP DEFAULT now(),
    
    UNIQUE(resource, action)
);

CREATE TABLE core.role_permissions (
    role VARCHAR(50) NOT NULL,  -- 'admin', 'user', 'finance', 'technician'
    permission_id UUID NOT NULL REFERENCES core.permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT now(),
    
    PRIMARY KEY (role, permission_id)
);

-- Seed de permissões padrão
INSERT INTO core.permissions (resource, action, description) VALUES
    ('orders', 'create', 'Criar pedidos'),
    ('orders', 'read', 'Visualizar pedidos'),
    ('orders', 'update', 'Atualizar pedidos'),
    ('orders', 'delete', 'Deletar pedidos'),
    ('orders', 'restore', 'Restaurar pedidos deletados'),
    ('financial', 'create', 'Criar lançamentos financeiros'),
    ('financial', 'read', 'Visualizar lançamentos'),
    ('financial', 'update', 'Atualizar lançamentos'),
    ('financial', 'delete', 'Deletar lançamentos'),
    ('audit', 'read', 'Visualizar audit logs'),
    ('users', 'create', 'Criar usuários'),
    ('users', 'read', 'Visualizar usuários'),
    ('users', 'update', 'Atualizar usuários'),
    ('users', 'delete', 'Deletar usuários');

-- Seed de permissões para role 'admin' (todas)
INSERT INTO core.role_permissions (role, permission_id)
SELECT 'admin', id FROM core.permissions;

-- Seed de permissões para role 'user' (básicas)
INSERT INTO core.role_permissions (role, permission_id)
SELECT 'user', id FROM core.permissions 
WHERE resource IN ('orders', 'financial') AND action IN ('create', 'read', 'update');
```

**Testes:**
- Migration up/down
- Seeds criados corretamente
- Admin tem todas as permissões

---

#### ✅ **Commit 12: Models - Permission e RolePermission**

**Arquivo:** `backend/app/models/permission.py`

```python
from sqlalchemy import Column, VARCHAR, Text, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    resource = Column(VARCHAR(50), nullable=False)
    action = Column(VARCHAR(50), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=text("now()"))
```

**Arquivo:** `backend/app/models/role_permission.py`

```python
from sqlalchemy import Column, VARCHAR, ForeignKey, TIMESTAMP, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        PrimaryKeyConstraint("role", "permission_id"),
        {"schema": "core"}
    )
    
    role = Column(VARCHAR(50), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("core.permissions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"))
```

---

#### ✅ **Commit 13: Security - Decorator @require_permission**

**Arquivo:** `backend/app/security/rbac.py`

```python
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role_permission import RolePermission
from app.models.permission import Permission
from app.security.deps import get_db
from app.auth import get_current_user

def has_permission(user: User, resource: str, action: str, db: Session) -> bool:
    """
    Verifica se user tem permissão específica.
    
    Consulta: core.role_permissions JOIN core.permissions
    """
    permission = db.query(Permission).filter(
        Permission.resource == resource,
        Permission.action == action
    ).first()
    
    if not permission:
        return False  # Permissão não existe no sistema
    
    role_perm = db.query(RolePermission).filter(
        RolePermission.role == user.role,
        RolePermission.permission_id == permission.id
    ).first()
    
    return role_perm is not None

def require_permission(resource: str, action: str):
    """
    Decorator para exigir permissão em rotas.
    
    Uso:
        @router.delete("/{id}")
        @require_permission("orders", "delete")
        def delete_order(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db),
            **kwargs
        ):
            if not has_permission(current_user, resource, action, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissão negada: {resource}:{action}"
                )
            return await func(*args, current_user=current_user, db=db, **kwargs)
        return wrapper
    return decorator
```

**Testes:**
- `test_has_permission_admin()` - Admin tem todas
- `test_has_permission_user_limited()` - User tem só básicas
- `test_require_permission_decorator()` - 403 se sem permissão

---

#### ✅ **Commit 14: Routes - Aplicar @require_permission**

**Arquivo:** `backend/app/routers/order_routes.py`

```python
from app.security.rbac import require_permission

@router.post("", status_code=status.HTTP_201_CREATED)
@require_permission("orders", "create")
def create_order(...):
    ...

@router.patch("/{order_id}")
@require_permission("orders", "update")
def update_order(...):
    ...

@router.delete("/{order_id}")
@require_permission("orders", "delete")
def delete_order(...):
    ...

@router.post("/{order_id}/restore")
@require_permission("orders", "restore")
def restore_order(...):
    ...
```

**Similar para:**
- `backend/app/routers/financial_routes.py`
- `backend/app/routers/audit_routes.py`
- `backend/app/routers/user_routes.py`

**Testes:**
- `test_order_create_requires_permission()` - User sem permissão → 403
- `test_order_delete_requires_permission()` - Technician sem delete → 403
- `test_admin_has_all_permissions()` - Admin passa em tudo

---

#### ✅ **Commit 15: Routes - API de gerenciamento de permissões (admin)**

**Arquivo:** `backend/app/routers/rbac_routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.security.deps import get_db
from app.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/rbac", tags=["RBAC (Admin Only)"])

@router.get("/permissions")
def list_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todas as permissões do sistema (ADMIN ONLY)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    permissions = db.query(Permission).all()
    return {
        "items": [
            {
                "id": str(p.id),
                "resource": p.resource,
                "action": p.action,
                "description": p.description
            }
            for p in permissions
        ]
    }

@router.get("/roles/{role}/permissions")
def list_role_permissions(
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista permissões de uma role específica (ADMIN ONLY)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    role_perms = db.query(RolePermission).filter(
        RolePermission.role == role
    ).all()
    
    permission_ids = [rp.permission_id for rp in role_perms]
    permissions = db.query(Permission).filter(
        Permission.id.in_(permission_ids)
    ).all()
    
    return {
        "role": role,
        "permissions": [
            f"{p.resource}:{p.action}"
            for p in permissions
        ]
    }

@router.post("/roles/{role}/permissions/{resource}/{action}")
def grant_permission(
    role: str,
    resource: str,
    action: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Concede permissão a uma role (ADMIN ONLY)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Buscar permission
    permission = db.query(Permission).filter(
        Permission.resource == resource,
        Permission.action == action
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não existe")
    
    # Verificar se já existe
    existing = db.query(RolePermission).filter(
        RolePermission.role == role,
        RolePermission.permission_id == permission.id
    ).first()
    
    if existing:
        return {"ok": True, "message": "Permissão já concedida"}
    
    # Criar role_permission
    role_perm = RolePermission(role=role, permission_id=permission.id)
    db.add(role_perm)
    db.commit()
    
    return {"ok": True, "message": f"Permissão {resource}:{action} concedida a {role}"}

@router.delete("/roles/{role}/permissions/{resource}/{action}")
def revoke_permission(
    role: str,
    resource: str,
    action: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoga permissão de uma role (ADMIN ONLY)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Buscar permission
    permission = db.query(Permission).filter(
        Permission.resource == resource,
        Permission.action == action
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não existe")
    
    # Remover role_permission
    db.query(RolePermission).filter(
        RolePermission.role == role,
        RolePermission.permission_id == permission.id
    ).delete()
    db.commit()
    
    return {"ok": True, "message": f"Permissão {resource}:{action} revogada de {role}"}
```

**Testes:**
- `test_grant_permission()` - Conceder funciona
- `test_revoke_permission()` - Revogar remove
- `test_list_role_permissions()` - Lista corretamente

---

## 📋 Commit 16: Docs + README

**Atualizar:**
- `docs/ETAPA_6_CONCLUSAO.md` - Documento técnico completo
- `backend/README_TESTS.md` - Novas seções de teste (audit, soft delete, rbac)
- `README.md` - Features enterprise adicionadas

---

## 🎯 Cronograma de Commits

| # | Commit | Descrição | Arquivos | Testes |
|---|--------|-----------|----------|--------|
| 1 | `feat(audit): add audit_logs migration` | Migration tabela audit_logs | `003_create_audit_logs.py` | Migration up/down |
| 2 | `feat(audit): add AuditLog model` | Model SQLAlchemy | `models/audit_log.py` | Model creation |
| 3 | `feat(audit): add AuditService` | Service centralizado | `services/audit_service.py` | log_create/update/delete |
| 4 | `feat(audit): integrate with OrderService` | Auto-audit em CRUD | `services/order_service.py` | Audit logs criados |
| 5 | `feat(audit): add audit routes (admin)` | Endpoint consulta | `routers/audit_routes.py` | Admin only, filtros |
| 6 | `feat(soft-delete): add deleted_at columns` | Migration soft delete | `004_add_soft_delete.py` | Migration up/down |
| 7 | `feat(soft-delete): update models` | Order/Financial models | `models/order.py`, `models/financial_entry.py` | is_deleted property |
| 8 | `feat(soft-delete): update repositories` | Queries com filtro | `repositories/*.py` | include_deleted |
| 9 | `feat(soft-delete): update services` | Soft delete logic | `services/order_service.py` | Soft delete funciona |
| 10 | `feat(soft-delete): add restore endpoint` | POST /orders/{id}/restore | `routers/order_routes.py` | Restore admin only |
| 11 | `feat(rbac): add permissions tables` | Migration RBAC | `005_create_rbac_tables.py` | Seeds corretos |
| 12 | `feat(rbac): add Permission models` | Models RBAC | `models/permission.py` | Model creation |
| 13 | `feat(rbac): add @require_permission` | Decorator segurança | `security/rbac.py` | has_permission |
| 14 | `feat(rbac): apply permissions to routes` | Proteger endpoints | `routers/*.py` | 403 sem permissão |
| 15 | `feat(rbac): add permission management API` | CRUD permissões | `routers/rbac_routes.py` | Grant/revoke |
| 16 | `docs: add ETAPA 6 documentation` | Docs completas | `docs/*`, `README*.md` | - |

**Total:** 16 commits semânticos

---

## 🚨 Breaking Changes

### **1. Soft Delete (Impacto Médio)**

**ANTES:**
```python
DELETE /orders/{id}  # Hard delete (remove do banco)
GET /orders          # Retorna todos
```

**DEPOIS:**
```python
DELETE /orders/{id}  # Soft delete (marca deleted_at)
GET /orders          # Retorna apenas ativos (deleted_at IS NULL)
GET /orders?include_deleted=true  # Admin vê deletados também
POST /orders/{id}/restore  # Restaurar (admin only)
```

**Migração:** Transparente (API externa não muda behavior)

---

### **2. RBAC (Impacto Alto)**

**ANTES:**
```python
# Role hardcoded em if/else
if current_user.role != "admin":
    raise HTTPException(403)
```

**DEPOIS:**
```python
# Role configurável via banco
@require_permission("orders", "delete")
def delete_order(...):
    ...
```

**Migração:** Seeds criam permissões padrão (admin = todas, user = básicas)

---

## ✅ Acceptance Criteria

### **ETAPA 6 completa quando:**

- [ ] 16 commits realizados
- [ ] 5 migrations aplicadas (003 a 007)
- [ ] 42 + N testes passando (N = novos testes de audit/soft-delete/rbac)
- [ ] Coverage ≥ 75%
- [ ] CI/CD verde
- [ ] Docs atualizadas (ETAPA_6_CONCLUSAO.md, README_TESTS.md)
- [ ] Zero warnings
- [ ] Backward compatibility mantida (sem breaking changes não documentados)

---

## 📊 Estimativa de Esforço

| Feature | Commits | Migrations | Testes Novos | Tempo Estimado |
|---------|---------|------------|--------------|----------------|
| Audit Log | 5 | 1 | ~15 | 3-4h |
| Soft Delete | 5 | 1 | ~12 | 2-3h |
| RBAC | 5 | 1 | ~10 | 2-3h |
| Docs | 1 | 0 | 0 | 1h |
| **TOTAL** | **16** | **3** | **~37** | **8-11h** |

---

## 🎯 Próxima Ação

**Iniciar com Commit 1:**

```bash
# Criar nova feature branch
git checkout -b feature/etapa-6-enterprise

# Criar migration audit_logs
alembic revision -m "create_audit_logs_table"
# Editar arquivo 003_create_audit_logs.py
```

**Confirme para eu começar a implementação!** 🚀

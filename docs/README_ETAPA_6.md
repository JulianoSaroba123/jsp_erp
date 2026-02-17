# ETAPA 6 — Enterprise (Runbook Executável)
Objetivo: elevar o backend para padrão enterprise com **Audit Log**, **Soft Delete** e **RBAC** sem quebrar contratos existentes e mantendo CI 100% verde.

---

## 0) Pré-requisitos
- Python 3.11+ (ou a versão padrão do projeto)
- PostgreSQL 15+
- Alembic configurado e funcionando
- CI (GitHub Actions) rodando com banco de teste (DATABASE_URL)

> Convenção: comandos abaixo assumem execução em `backend/`

---

## 1) Escopo da ETAPA 6 (3 features)
### 1.1 Audit Log (compliance + rastreabilidade)
Registrar eventos críticos com:
- entity/resource (ex: `orders`, `financial_entries`, `users`)
- entity_id
- action (ex: `create`, `update`, `delete`, `restore`, `pay`, etc.)
- before/after em JSONB
- user_id (quando autenticado)
- request_id (middleware já fornece)
- created_at
- indexes estratégicos para query

### 1.2 Soft Delete (corporativo)
Remoção lógica com:
- `deleted_at`, `deleted_by`
- filtros padrão (listar só `deleted_at IS NULL`)
- restore admin
- índices parciais para performance

### 1.3 RBAC (permissions enterprise)
Modelo:
- permissions = `resource:action` (ex: `orders:delete`)
- roles N:N permissions
- users N:N roles
- decorator clean: `@require_permission("orders:delete")`
- seeds: admin full access, user limitado

---

## 2) Migrations previstas (Alembic)
### Migration 003 — Audit Log
```bash
alembic revision -m "create_audit_logs_table"
```

**SQL esperado:**
```sql
CREATE TABLE core.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES core.users(id),
    action VARCHAR(50) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    before JSONB,
    after JSONB,
    request_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_audit_user ON core.audit_logs(user_id);
CREATE INDEX idx_audit_entity ON core.audit_logs(entity, entity_id);
CREATE INDEX idx_audit_created ON core.audit_logs(created_at DESC);
CREATE INDEX idx_audit_request ON core.audit_logs(request_id);
```

### Migration 004 — Soft Delete
```bash
alembic revision -m "add_soft_delete_columns"
```

**SQL esperado:**
```sql
ALTER TABLE core.orders 
ADD COLUMN deleted_at TIMESTAMP,
ADD COLUMN deleted_by UUID REFERENCES core.users(id);

ALTER TABLE core.financial_entries
ADD COLUMN deleted_at TIMESTAMP,
ADD COLUMN deleted_by UUID REFERENCES core.users(id);

-- Índices parciais (performance)
CREATE INDEX idx_orders_active ON core.orders(user_id, created_at DESC) 
WHERE deleted_at IS NULL;

CREATE INDEX idx_financial_active ON core.financial_entries(user_id, occurred_at DESC)
WHERE deleted_at IS NULL;
```

### Migration 005 — RBAC
```bash
alembic revision -m "create_rbac_tables"
```

**SQL esperado:**
```sql
CREATE TABLE core.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE core.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(resource, action)
);

CREATE TABLE core.role_permissions (
    role_id UUID REFERENCES core.roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES core.permissions(id) ON DELETE CASCADE,
    PRIMARY KEY(role_id, permission_id)
);

CREATE TABLE core.user_roles (
    user_id UUID REFERENCES core.users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES core.roles(id) ON DELETE CASCADE,
    PRIMARY KEY(user_id, role_id)
);

-- Seeds iniciais
INSERT INTO core.roles (name, description) VALUES
('admin', 'Administrador com acesso total'),
('user', 'Usuário padrão com acesso limitado');

INSERT INTO core.permissions (resource, action) VALUES
('orders', 'create'),
('orders', 'read'),
('orders', 'update'),
('orders', 'delete'),
('orders', 'restore'),
('financial', 'create'),
('financial', 'read'),
('financial', 'update'),
('financial', 'delete'),
('audit', 'read'),
('users', 'manage_roles');

-- Admin tem tudo
INSERT INTO core.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM core.roles r, core.permissions p WHERE r.name = 'admin';

-- User tem CRUD básico (sem delete/restore/audit)
INSERT INTO core.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM core.roles r, core.permissions p 
WHERE r.name = 'user' 
AND (resource, action) IN (
    ('orders', 'create'),
    ('orders', 'read'),
    ('orders', 'update'),
    ('financial', 'read')
);
```

---

## 3) Endpoints afetados
### 3.1 Novos endpoints
**Audit**
- `GET /audit?entity=orders&entity_id={uuid}` (admin-only)
- `GET /audit?request_id={uuid}` (admin-only)
- `GET /audit?user_id={uuid}&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` (admin-only)

**Soft delete**
- `POST /orders/{id}/restore` (admin-only)
- `POST /financial/entries/{id}/restore` (admin-only)
- `GET /orders?include_deleted=true` (admin-only)

**RBAC**
- `GET /roles` (admin)
- `POST /roles` (admin)
- `GET /roles/{id}/permissions` (admin)
- `POST /roles/{id}/permissions` (admin - grant)
- `DELETE /roles/{id}/permissions/{permission_id}` (admin - revoke)
- `GET /users/{id}/roles` (admin)
- `POST /users/{id}/roles` (admin - assign)
- `DELETE /users/{id}/roles/{role_id}` (admin - unassign)

### 3.2 Endpoints modificados (comportamento)
**Breaking changes (documentar no PR):**
- `GET /orders` → retorna apenas `deleted_at IS NULL` (antes: todos)
- `GET /financial/entries` → retorna apenas `deleted_at IS NULL`
- `DELETE /orders/{id}` → soft delete (antes: hard delete)
- `DELETE /financial/entries/{id}` → soft delete (antes: hard delete)

**Compatibilidade mantida:**
- Status codes (403/404/409) preservados
- Response schemas inalterados
- Query params existentes funcionam normalmente

---

## 4) Regras de implementação (padrão)
### 4.1 Audit log — quando registrar
**Eventos obrigatórios:**
- `create` (orders, financial_entries, users)
- `update` (orders, financial_entries)
- `delete` (soft delete)
- `restore` (admin undo soft delete)
- `pay` / `unpay` (financial_entries status change)

**Formato do audit:**
```python
# Service layer
from app.services.audit_service import AuditService

audit = AuditService()

# Before update
before_snapshot = {
    "total": order.total,
    "description": order.description,
    "status": financial_entry.status if financial_entry else None
}

# ... apply changes ...

# After update
after_snapshot = {
    "total": order.total,
    "description": order.description,
    "status": financial_entry.status if financial_entry else None
}

audit.log(
    user_id=current_user.id,
    action="update",
    entity="orders",
    entity_id=order.id,
    before=before_snapshot,
    after=after_snapshot,
    request_id=request.state.request_id
)
```

**Dados sensíveis (NUNCA incluir):**
- password_hash
- access_token / refresh_token
- PII desnecessário

### 4.2 Soft delete — filtro default
**Repository pattern:**
```python
class OrderRepository:
    @staticmethod
    def get_all(db: Session, user_id: UUID, include_deleted: bool = False):
        query = db.query(Order).filter(Order.user_id == user_id)
        
        if not include_deleted:
            query = query.filter(Order.deleted_at.is_(None))
        
        return query.order_by(Order.created_at.desc()).all()
    
    @staticmethod
    def soft_delete(db: Session, order: Order, deleted_by: UUID):
        order.deleted_at = datetime.utcnow()
        order.deleted_by = deleted_by
        db.commit()
    
    @staticmethod
    def restore(db: Session, order: Order):
        order.deleted_at = None
        order.deleted_by = None
        db.commit()
```

### 4.3 RBAC — enforcement
**Decorator pattern:**
```python
# app/security/decorators.py
from functools import wraps
from fastapi import HTTPException, status

def require_permission(resource: str, action: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=None, db=None, **kwargs):
            # Check if user has permission
            has_perm = check_permission(db, current_user.id, resource, action)
            
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Você não tem permissão para {action} em {resource}"
                )
            
            return await func(*args, current_user=current_user, db=db, **kwargs)
        
        return wrapper
    return decorator

# Usage in router
@router.delete("/{id}")
@require_permission("orders", "delete")
def delete_order(id: UUID, current_user: User = Depends(get_current_user), ...):
    # Implementation
    pass
```

**Checagem de permissão:**
```python
def check_permission(db: Session, user_id: UUID, resource: str, action: str) -> bool:
    # Query: user → roles → permissions
    result = db.execute(text("""
        SELECT 1
        FROM core.user_roles ur
        JOIN core.role_permissions rp ON ur.role_id = rp.role_id
        JOIN core.permissions p ON rp.permission_id = p.id
        WHERE ur.user_id = :user_id
        AND p.resource = :resource
        AND p.action = :action
        LIMIT 1
    """), {"user_id": user_id, "resource": resource, "action": action})
    
    return result.fetchone() is not None
```

---

## 5) Plano de rollout (dev → staging → prod)
### 5.1 Dev (local)
```bash
# 1. Criar branch
git checkout main
git pull
git checkout -b feature/etapa-6-enterprise

# 2. Criar migrations
cd backend
alembic revision -m "create_audit_logs_table"
# Editar arquivo gerado com SQL da seção 2.1

alembic revision -m "add_soft_delete_columns"
# Editar arquivo gerado com SQL da seção 2.2

alembic revision -m "create_rbac_tables"
# Editar arquivo gerado com SQL da seção 2.3

# 3. Aplicar migrations
alembic upgrade head

# 4. Verificar estrutura
psql $DATABASE_URL -c "\dt core.*"
psql $DATABASE_URL -c "SELECT * FROM core.roles;"
```

### 5.2 Testes (local)
```bash
# Rodar suite completa
cd backend
.venv/Scripts/Activate.ps1  # Windows
# ou: source .venv/bin/activate  # Linux/Mac

# Com DATABASE_URL_TEST setado
$env:DATABASE_URL_TEST="postgresql://user:pass@localhost:5432/jsp_erp_test"
pytest tests/ -v --cov=app --cov-report=term-missing

# Esperado: 42 + N testes passando (N = novos testes da ETAPA 6)
# Coverage: >= 75%
```

### 5.3 Staging (GitHub Actions + Deploy)
```bash
# 1. Commit + Push
git add .
git commit -m "feat(enterprise): audit log + soft delete + RBAC"
git push origin feature/etapa-6-enterprise

# 2. Abrir PR
# GitHub: compare feature/etapa-6-enterprise → main

# 3. Aguardar CI verde
# Checks devem passar:
# ✅ pytest (42+N testes)
# ✅ coverage >= 75%
# ✅ migrations OK

# 4. Code review
# Solicitar aprovação do time

# 5. Merge
# Squash and merge (ou merge commit, conforme padrão do time)

# 6. Deploy staging
# Via Render/Heroku/outro:
# - Pull main
# - Run migrations: alembic upgrade head
# - Restart app
```

### 5.4 Validação staging
```bash
# Smoke tests (Postman/curl/httpie)

# 1. Criar pedido (deve auditar)
POST https://staging.example.com/orders
Authorization: Bearer {token}
{
  "description": "Test order",
  "total": 100
}

# 2. Verificar audit log (admin)
GET https://staging.example.com/audit?entity=orders
Authorization: Bearer {admin_token}

# Esperado: registro de "create" com before=null, after={...}

# 3. Soft delete
DELETE https://staging.example.com/orders/{id}

# 4. Verificar não aparece em listagem
GET https://staging.example.com/orders
# Esperado: order deletado não aparece

# 5. Restore (admin)
POST https://staging.example.com/orders/{id}/restore
Authorization: Bearer {admin_token}

# 6. RBAC - tentar ação sem permissão
DELETE https://staging.example.com/orders/{outro_id}
Authorization: Bearer {user_token}
# Esperado: 403 Forbidden
```

### 5.5 Produção
```bash
# 1. Backup do banco ANTES
pg_dump $DATABASE_URL > backup_pre_etapa6_$(date +%Y%m%d_%H%M%S).sql

# 2. Deploy (mesmo processo de staging)
git checkout main
git pull
# Render auto-deploy OU manual:
# ssh prod-server
# cd /app
# git pull
# source venv/bin/activate
# alembic upgrade head
# systemctl restart app

# 3. Smoke tests (prod)
# Repetir validações da seção 5.4

# 4. Monitoramento (primeiras 2h)
# - Logs de erro (Sentry/CloudWatch)
# - Performance (query time de reports)
# - Usuários reportando 403 inesperados

# 5. Rollback plan (se necessário)
alembic downgrade -1  # Ou downgrade específico
# Restore backup se crítico
```

---

## 6) Checklist de testes (unit + integration)
### 6.1 Audit Log
**Testes unitários:**
- [ ] `test_audit_service_log_create()`
- [ ] `test_audit_service_log_update()`
- [ ] `test_audit_service_log_delete()`
- [ ] `test_audit_jsonb_serialization()`

**Testes de integração:**
- [ ] `test_order_create_audits_correctly()`
- [ ] `test_order_update_audits_before_after()`
- [ ] `test_delete_audits_with_snapshot()`
- [ ] `test_audit_query_by_entity()`
- [ ] `test_audit_query_by_request_id()`
- [ ] `test_audit_admin_only_access()`

### 6.2 Soft Delete
**Testes unitários:**
- [ ] `test_repository_soft_delete()`
- [ ] `test_repository_filter_active_only()`
- [ ] `test_repository_include_deleted_flag()`
- [ ] `test_repository_restore()`

**Testes de integração:**
- [ ] `test_delete_order_soft_deletes()`
- [ ] `test_list_orders_excludes_deleted()`
- [ ] `test_admin_list_with_include_deleted()`
- [ ] `test_restore_order_admin_only()`
- [ ] `test_get_deleted_order_returns_404()`
- [ ] `test_delete_already_deleted_is_idempotent()`

### 6.3 RBAC
**Testes unitários:**
- [ ] `test_check_permission_returns_true_when_granted()`
- [ ] `test_check_permission_returns_false_when_denied()`
- [ ] `test_admin_has_all_permissions()`
- [ ] `test_user_has_limited_permissions()`

**Testes de integração:**
- [ ] `test_delete_order_requires_permission()`
- [ ] `test_user_without_delete_permission_gets_403()`
- [ ] `test_admin_can_delete_any_order()`
- [ ] `test_grant_permission_to_role()`
- [ ] `test_revoke_permission_from_role()`
- [ ] `test_assign_role_to_user()`
- [ ] `test_unassign_role_from_user()`

**Total esperado:** ~37 novos testes

---

## 7) Breaking changes (documentar no PR)
### 7.1 Comportamento de DELETE
**Antes:**
```python
DELETE /orders/{id}  # Hard delete (remove do banco)
```

**Depois:**
```python
DELETE /orders/{id}  # Soft delete (seta deleted_at)
```

**Migração:** Hard delete ainda possível via flag admin (se implementado):
```python
DELETE /orders/{id}?hard=true  # Admin-only (opcional)
```

### 7.2 Listagens retornam apenas ativos
**Antes:**
```python
GET /orders  # Retorna todos (incluindo deletados se existissem)
```

**Depois:**
```python
GET /orders  # Retorna apenas deleted_at IS NULL
GET /orders?include_deleted=true  # Admin pode ver deletados
```

**Migração:** Nenhuma ação necessária - comportamento esperado é melhorado.

### 7.3 Permissões via RBAC
**Antes:**
```python
# Hardcoded no código
if current_user.role == "admin":
    # allow delete
```

**Depois:**
```python
# Database-driven
@require_permission("orders", "delete")
def delete_order(...):
```

**Migração:** Seeds garantem que roles existentes (admin/user) mantêm permissões atuais.

---

## 8) Critérios de aceite (gate de qualidade)
### 8.1 Testes
- [ ] **42 + 37 = 79 testes passando** (ou mais)
- [ ] **Coverage >= 75%** (manter ou superar baseline)
- [ ] **0 warnings** no pytest
- [ ] **CI verde** no GitHub Actions

### 8.2 Performance
- [ ] Queries de listagem (GET /orders) < 200ms (p95)
- [ ] Audit log insert < 10ms (não bloquear transação principal)
- [ ] RBAC check < 5ms (cache considerado se necessário)

### 8.3 Funcional
- [ ] Audit log registra create/update/delete
- [ ] Soft delete não remove dados fisicamente
- [ ] Restore funciona corretamente (admin)
- [ ] RBAC bloqueia ações não autorizadas (403)
- [ ] Admin mantém acesso total
- [ ] User mantém acesso limitado (compatibilidade)

### 8.4 Segurança
- [ ] Audit log NÃO expõe senhas/tokens
- [ ] Endpoints admin protegidos (403 para users)
- [ ] Anti-enumeration mantido (404 em vez de 403 quando apropriado)
- [ ] CORS/rate limiting não afetados

### 8.5 Documentação
- [ ] README_ETAPA_6.md completo (este arquivo)
- [ ] CHANGELOG.md atualizado com breaking changes
- [ ] PR description com resumo executivo
- [ ] Migrations comentadas (via docstrings em alembic)

---

## 9) Rollback plan (contingência)
### 9.1 Rollback de código (GitHub)
```bash
# Se deploy falhou ou bugs críticos
git revert {commit_hash}
git push origin main
# Redeploy automático (Render) ou manual
```

### 9.2 Rollback de migrations (Alembic)
```bash
# Identificar versão atual
alembic current

# Downgrade para versão anterior à ETAPA 6
# Exemplo: se última migration era 002_xxx
alembic downgrade 002_add_orders_updated_at

# Verificar
psql $DATABASE_URL -c "\dt core.*"
# Não deve ter: audit_logs, roles, permissions, etc.
```

### 9.3 Restaurar backup (emergência)
```bash
# Se rollback de migration falhou
# 1. Parar aplicação
systemctl stop app  # OU equivalente

# 2. Restaurar backup
psql $DATABASE_URL < backup_pre_etapa6_YYYYMMDD_HHMMSS.sql

# 3. Reverter código para commit anterior
git reset --hard {commit_antes_etapa6}
git push -f origin main  # CUIDADO: force push

# 4. Restart app
systemctl start app
```

**Critério para rollback total:**
- > 5% de requests retornando 500
- Perda de dados detectada
- Migrations irreversíveis com erro

---

## 10) Contatos e suporte
**Tech Lead:** [Nome]  
**DevOps:** [Nome]  
**DBA:** [Nome] (para emergências de migration)

**Canais:**
- Slack: #backend-enterprise
- Incident: PagerDuty / outro

**Horário de deploy recomendado:**
- Terça a quinta, 10h-14h (horário comercial, time disponível)
- **EVITAR:** sexta, véspera de feriado, após 16h

---

## 11) Métricas de sucesso (1 semana pós-deploy)
- [ ] **Zero incidents P0/P1** relacionados à ETAPA 6
- [ ] **Audit log com > 1000 registros** (usuários auditados)
- [ ] **Soft delete sendo usado** (> 10 orders deletados e restaurados)
- [ ] **RBAC funcionando** (> 5 tentativas de 403 capturadas corretamente)
- [ ] **Performance mantida** (p95 queries < 200ms)
- [ ] **Coverage estável** (>= 75%)

---

## 12) Próximos passos (pós-ETAPA 6)
### 12.1 Iteração imediata
- [ ] Dashboard de audit log (UI para admin visualizar eventos)
- [ ] Bulk restore (admin restaurar vários registros de uma vez)
- [ ] Permission groups (simplificar atribuição de roles)

### 12.2 Médio prazo
- [ ] Integração com templates (frontend consumindo novos endpoints)
- [ ] Exportação de audit log (CSV/Excel para compliance)
- [ ] Webhooks para eventos auditados (integrações externas)

### 12.3 Longo prazo
- [ ] Multi-tenancy full (isolamento por tenant_id)
- [ ] RBAC dinâmico (criar permissions via UI)
- [ ] Audit log retention policy (archive logs > 90 dias)

---

**Versão:** 1.0  
**Última atualização:** 17 de fevereiro de 2026  
**Autor:** Time Backend ERP JSP  
**Status:** READY FOR EXECUTION ✅

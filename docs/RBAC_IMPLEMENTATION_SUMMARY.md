# RBAC Implementation Summary - ETAPA 6

## ✅ O que foi implementado

### 1. Migration RBAC (004_add_rbac.py)
- Cria 4 tabelas no schema `core`:
  - `roles`: Papéis do sistema (admin, user, finance, etc)
  - `permissions`: Permissões individuais (resource:action)
  - `user_roles`: Many-to-many entre users e roles
  - `role_permissions`: Many-to-many entre roles e permissions
- Cria 5 índices para otimização de queries
- Status: **Criada, não aplicada ainda**

### 2. Models

#### Permission Model (`app/models/permission.py`)
```python
class Permission:
    id: UUID
    resource: str  # Ex: "orders", "financial"
    action: str    # Ex: "read", "create", "update", "delete"
    description: str (opcional)
    full_name: str  # Property -> "orders:delete"
```

#### Role Model (`app/models/role.py`)
```python
class Role:
    id: UUID
    name: str (UNIQUE)
    description: str (opcional)
    permissions: relationship -> list[Permission]
    users: relationship -> list[User]
```

#### User Model (atualizado)
```python
class User:
    # ... campos existentes ...
    roles: relationship -> list[Role]
    
    def has_permission(resource: str, action: str) -> bool:
        # Verifica se user tem permissão através das roles
```

### 3. Security Dependency

#### `require_permission(resource, action)`
- Factory que retorna dependency async
- Usa `get_current_user` internamente
- Verifica `user.has_permission(resource, action)`
- Retorna 403 Forbidden se não tiver permissão

**Uso:**
```python
@router.delete("/{order_id}")
async def delete_order(
    order_id: UUID,
    current_user: User = Depends(require_permission("orders", "delete")),
    db: Session = Depends(get_db)
):
    # ...
```

### 4. Enforcement Aplicado

- [order_routes.py](../backend/app/routers/order_routes.py#L115): `DELETE /orders/{id}` agora requer permissão `orders:delete`

### 5. Seed Script

**Arquivo:** [backend/app/scripts/seed_rbac.py](../backend/app/scripts/seed_rbac.py)

**Popula:**
- 14 permissions (orders, users, financial, reports)
- 3 roles:
  - `admin`: Todas as permissões
  - `user`: Permissões básicas (sem delete)
  - `finance`: Foco em financeiro + leitura de orders
- Atribui roles aos users existentes baseado no campo `role` (legado)

**Execução:**
```powershell
cd backend
python -m app.scripts.seed_rbac
```

### 6. Testes

**Arquivo:** [backend/tests/test_rbac.py](../backend/tests/test_rbac.py)

**Cenários:**
- ✅ User sem permissão recebe 403 ao tentar DELETE order
- ✅ Admin com permissão consegue DELETE order
- ✅ `User.has_permission()` funciona corretamente
- ✅ Associations many-to-many funcionam

**Execução:**
```powershell
cd backend
pytest tests/test_rbac.py -v
```

---

## 🚀 Próximos passos (ordem de execução)

### 1. Aplicar migration 004
```powershell
cd backend
alembic upgrade head
```

**Valida:**
```powershell
alembic current
# Deve mostrar: 004_add_rbac (head)
```

### 2. Popular roles e permissions (seeds)
```powershell
cd backend
python -m app.scripts.seed_rbac
```

**Saída esperada:**
```
[1/3] Criando permissions...
   + Criada permission: orders:read
   + Criada permission: orders:create
   ...
[2/3] Criando roles...
   + Criada role: admin
   + Criada role: user
   ...
[3/3] Atribuindo roles aos usuários existentes...
   + Atribuída role 'admin' ao usuário admin@example.com
   ...
✓ SEED COMPLETO
```

### 3. Rodar testes de RBAC
```powershell
cd backend
pytest tests/test_rbac.py -v
```

**Esperado:** Todos os testes passam ✅

### 4. Testar manualmente via Swagger/Postman

**Cenário 1: User sem permissão**
```bash
POST /auth/login
{
  "username": "user@example.com",
  "password": "password"
}

# Copiar token

DELETE /orders/{id}
Authorization: Bearer {token}

# Resposta esperada: 403 Forbidden
# {"detail": "Usuário não possui permissão orders:delete"}
```

**Cenário 2: Admin com permissão**
```bash
POST /auth/login
{
  "username": "admin@example.com",
  "password": "password"
}

# Copiar token

DELETE /orders/{id}
Authorization: Bearer {token}

# Resposta esperada: 200 OK ou 204 No Content
```

---

## 📋 Checklist Final

- [x] Migration 004 criada
- [x] Models (Permission, Role) criados
- [x] User model atualizado com `roles` relationship
- [x] `require_permission()` dependency implementada
- [x] Enforcement aplicado em DELETE /orders
- [x] Seed script criado
- [x] Testes criados
- [ ] **Migration aplicada no DB**
- [ ] **Seeds executados**
- [ ] **Testes executados e passando**
- [ ] **Teste manual realizado**

---

## 📁 Arquivos criados/modificados

### Criados:
- `backend/alembic/versions/004_add_rbac.py`
- `backend/app/models/role.py`
- `backend/app/models/permission.py`
- `backend/app/scripts/__init__.py`
- `backend/app/scripts/seed_rbac.py`
- `backend/tests/test_rbac.py`

### Modificados:
- `backend/app/models/user.py` (+ roles relationship + has_permission())
- `backend/app/security/deps.py` (+ require_permission())
- `backend/app/routers/order_routes.py` (DELETE endpoint protegido)

---

## 🛠️ Comandos rápidos

```powershell
# 1. Aplicar migration
cd backend
alembic upgrade head

# 2. Seed RBAC
python -m app.scripts.seed_rbac

# 3. Testar
pytest tests/test_rbac.py -v

# 4. Verificar logs
alembic current
alembic history
```

---

## ⚠️ Notas Importantes

1. **Migration 004 deve ser aplicada** antes de executar seeds ou testes
2. **Seed script é idempotente**: pode executar múltiplas vezes sem duplicar dados
3. **Testes assumem** que tabelas RBAC existem (migration aplicada)
4. **Campo `role` no User** é legado - novos sistemas devem usar apenas `roles` relationship
5. **Formato de permission**: sempre `resource:action` (ex: `orders:delete`)

---

## 🎯 Estado do Sistema

**Branch atual:** `feature/etapa-6-enterprise`

**Alembic HEAD:** `003_add_soft_delete` → deve ir para `004_add_rbac`

**Database:** `jsp_erp_test` schema `core` owner `jsp_user`

**Próximo passo:** `alembic upgrade head` + `python -m app.scripts.seed_rbac` + `pytest tests/test_rbac.py -v`

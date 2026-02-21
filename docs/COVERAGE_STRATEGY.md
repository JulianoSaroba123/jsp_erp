# 📈 ESTRATÉGIA DE COVERAGE - PLANO DE 3 SPRINTS

## 🎯 Metas Progressivas

| Sprint | Meta Coverage | Foco | Duração |
|--------|---------------|------|---------|
| **Sprint 1** | 70% | Foundation (Services + Auth) | 1 semana |
| **Sprint 2** | 75% | Integration (Repositories + Middleware) | 1 semana |
| **Sprint 3** | 80% | Edge Cases (Error Handling + Utils) | 1 semana |

---

## 📊 Baseline Atual

**Como descobrir o coverage atual:**

1. Vá em: https://github.com/JulianoSaroba123/jsp_erp/actions
2. Clique na última execução bem-sucedida do workflow **tests**
3. Scroll até "Artifacts"
4. Download **coverage-report-html**
5. Abra `htmlcov/index.html`
6. Veja o % total no topo da página

**Estimativa conservadora:** ~60-65% (baseado em 63 testes)

---

## 🎯 Sprint 1: Foundation (Meta: 70%)

### Áreas Prioritárias

#### 1️⃣ **Services Layer** (Alta prioridade)
**Arquivos:**
- `app/services/user_service.py`
- `app/services/order_service.py`

**Testes a criar:**
```
tests/services/
├── test_user_service.py
│   ├── test_create_user_success
│   ├── test_create_user_duplicate_email
│   ├── test_update_user_not_found
│   ├── test_list_users_pagination
│   └── test_delete_user_cascade
│
└── test_order_service.py
    ├── test_create_order_with_items
    ├── test_patch_order_status
    ├── test_soft_delete_order
    ├── test_list_orders_filters
    └── test_calculate_financial_summary
```

**Estimativa:** +8-10% coverage

---

#### 2️⃣ **Auth Endpoints** (Crítico para segurança)
**Arquivo:** `app/auth/router.py`

**Testes a criar:**
```
tests/auth/
├── test_auth_router.py
│   ├── test_login_success
│   ├── test_login_invalid_credentials
│   ├── test_login_inactive_user
│   ├── test_token_refresh
│   ├── test_logout
│   └── test_password_reset_flow
```

**Estimativa:** +5-7% coverage

---

#### 3️⃣ **Security Module**
**Arquivo:** `app/auth/security.py`

**Testes a criar:**
```
tests/auth/
├── test_security.py
│   ├── test_hash_password_bcrypt
│   ├── test_verify_password_correct
│   ├── test_verify_password_wrong
│   ├── test_create_access_token
│   ├── test_decode_access_token_valid
│   └── test_decode_access_token_expired
```

**Estimativa:** +3-5% coverage

---

### ✅ Resultado Esperado Sprint 1
- Coverage: **68-72%** (meta: 70%)
- Arquivos críticos cobertos
- Base sólida para próximas sprints

---

## 🎯 Sprint 2: Integration (Meta: 75%)

### Áreas Prioritárias

#### 1️⃣ **Repositories Layer**
**Arquivos:**
- `app/repositories/user_repo.py`
- `app/repositories/order_repository.py`

**Testes a criar:**
```
tests/repositories/
├── test_user_repository.py
│   ├── test_get_by_email
│   ├── test_get_by_id_with_relationships
│   ├── test_update_partial
│   ├── test_soft_delete
│   └── test_query_with_filters
│
└── test_order_repository.py
    ├── test_create_with_transaction
    ├── test_update_status
    ├── test_get_with_items
    ├── test_list_paginated
    └── test_aggregate_financial_data
```

**Estimativa:** +4-6% coverage

---

#### 2️⃣ **Middleware**
**Arquivos:**
- `app/middleware/logging.py`
- `app/middleware/request_id.py`

**Testes a criar:**
```
tests/middleware/
├── test_logging_middleware.py
│   ├── test_request_logging
│   ├── test_response_logging
│   └── test_error_logging
│
└── test_request_id_middleware.py
    ├── test_generate_request_id
    ├── test_propagate_request_id
    └── test_request_id_in_response
```

**Estimativa:** +2-3% coverage

---

#### 3️⃣ **Exception Handlers**
**Arquivo:** `app/exceptions/handlers.py`

**Testes a criar:**
```
tests/exceptions/
├── test_handlers.py
│   ├── test_handle_validation_error
│   ├── test_handle_not_found_error
│   ├── test_handle_permission_error
│   ├── test_handle_database_error
│   └── test_generic_exception_handler
```

**Estimativa:** +2-3% coverage

---

### ✅ Resultado Esperado Sprint 2
- Coverage: **74-77%** (meta: 75%)
- Camadas de integração cobertas
- Error paths testados

---

## 🎯 Sprint 3: Edge Cases (Meta: 80%)

### Áreas Prioritárias

#### 1️⃣ **Soft Delete Scenarios**
**Testes a criar:**
```
tests/features/
├── test_soft_delete_cascade.py
│   ├── test_delete_user_soft_deletes_orders
│   ├── test_restore_user_restores_orders
│   ├── test_list_excludes_deleted
│   └── test_query_include_deleted_flag
```

**Estimativa:** +2-3% coverage

---

#### 2️⃣ **Pagination & Filtering**
**Arquivo:** `app/utils/pagination.py`

**Testes a criar:**
```
tests/utils/
├── test_pagination.py
│   ├── test_paginate_first_page
│   ├── test_paginate_last_page
│   ├── test_paginate_empty_result
│   ├── test_paginate_with_filters
│   └── test_pagination_metadata
```

**Estimativa:** +1-2% coverage

---

#### 3️⃣ **Financial Sync Paths**
**Testes a criar:**
```
tests/integration/
├── test_financial_sync.py
│   ├── test_order_create_updates_financial
│   ├── test_order_patch_recalculates_totals
│   ├── test_soft_delete_adjusts_balance
│   └── test_concurrent_updates_isolated
```

**Estimativa:** +2-3% coverage

---

### ✅ Resultado Esperado Sprint 3
- Coverage: **79-82%** (meta: 80%)
- Edge cases cobertos
- Pipeline confiável

---

## 🛠️ Implementação de Coverage Gate

### Fase 1: Coverage Report Sempre Visível (JÁ ATIVO ✅)

O workflow já gera HTML coverage. Apenas baixe e analise.

---

### Fase 2: Coverage Gate Progressivo (OPCIONAL)

**Adicionar no tests.yml:**

```yaml
- name: Run tests with coverage
  working-directory: backend
  run: |
    pytest --maxfail=1 --disable-warnings \
      --cov=app \
      --cov-report=term-missing \
      --cov-report=html \
      --cov-fail-under=65  # ← Começa conservador
```

**Cronograma de aumento:**

```
Semana 1-2:  --cov-fail-under=65  (baseline)
Semana 3-4:  --cov-fail-under=70  (Sprint 1 completo)
Semana 5-6:  --cov-fail-under=75  (Sprint 2 completo)
Semana 7-8:  --cov-fail-under=80  (Sprint 3 completo)
```

**⚠️ Importante:** Só aumente depois de confirmar que coverage atual está acima do novo limite!

---

### Fase 3: Coverage por Módulo (AVANÇADO)

**Adicionar pytest-cov config em `pyproject.toml` ou `.coveragerc`:**

```ini
[coverage:run]
source = app
omit = 
    */tests/*
    */__pycache__/*
    */migrations/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False

# Módulos críticos com metas individuais
fail_under = 70

[coverage:paths]
source = app/
```

---

## 📊 Dashboard de Acompanhamento

### Como Monitorar Coverage Semanal

**Planilha simples:**

| Semana | Coverage % | Testes Adicionados | Linhas Cobertas | Arquivos 100% |
|--------|------------|-------------------|-----------------|---------------|
| 0 (Atual) | ~65% | 63 | ? | ? |
| 1 | 68% | +12 | ? | 3 |
| 2 | 72% | +8 | ? | 5 |
| 3 | 75% | +10 | ? | 8 |
| 4 | 78% | +8 | ? | 10 |
| 5 | 80% | +6 | ? | 12 |

**Como coletar dados:**
1. Baixar artefato `coverage-report-html`
2. Abrir `index.html`
3. Anotar % total
4. Identificar arquivos com 100% (coluna verde)

---

## 🎯 Priorização de Arquivos

### Ordem de Importância (do mais para o menos crítico):

1. **Autenticação** (security.py, router.py) - Impacta segurança
2. **Services** (user_service.py, order_service.py) - Lógica core
3. **Repositories** (acesso a dados) - Integridade DB
4. **Exception Handlers** - Resposta a erros
5. **Middleware** - Logging e request tracking
6. **Utils** - Helpers e pagination

---

## ✅ Checklist de Implementação

### Sprint 1
- [ ] Baixar coverage atual e documentar baseline
- [ ] Criar `tests/services/test_user_service.py`
- [ ] Criar `tests/services/test_order_service.py`
- [ ] Criar `tests/auth/test_auth_router.py`
- [ ] Criar `tests/auth/test_security.py`
- [ ] Validar 70% atingido
- [ ] (Opcional) Adicionar `--cov-fail-under=65` no CI

### Sprint 2
- [ ] Criar `tests/repositories/test_user_repository.py`
- [ ] Criar `tests/repositories/test_order_repository.py`
- [ ] Criar `tests/middleware/test_logging_middleware.py`
- [ ] Criar `tests/exceptions/test_handlers.py`
- [ ] Validar 75% atingido
- [ ] (Opcional) Aumentar para `--cov-fail-under=70`

### Sprint 3
- [ ] Criar `tests/features/test_soft_delete_cascade.py`
- [ ] Criar `tests/utils/test_pagination.py`
- [ ] Criar `tests/integration/test_financial_sync.py`
- [ ] Validar 80% atingido
- [ ] (Opcional) Aumentar para `--cov-fail-under=75`
- [ ] Criar badge de coverage (shields.io)

---

## 🚀 Quick Wins (Coverage Fácil)

**Arquivos pequenos e simples para cobertura rápida:**

1. `app/utils/pagination.py` - Lógica pura, sem DB
2. `app/auth/security.py` - Funções isoladas
3. `app/schemas/*.py` - Validação Pydantic (teste inputs)

**Estratégia:** Comece por estes para boost rápido de %

---

## 🎓 Recursos para Escrever Testes

### Padrões já utilizados no projeto:
- Fixtures em `tests/conftest.py`
- TestClient do FastAPI
- Mocking com unittest.mock
- Factories com Faker

### Templates úteis:

**Service Test:**
```python
def test_create_user_success(db_session):
    service = UserService(db_session)
    user_data = {"name": "Test", "email": "test@example.com"}
    user = service.create(user_data)
    assert user.id is not None
    assert user.email == "test@example.com"
```

**Router Test:**
```python
def test_login_success(client, seed_user_admin):
    response = client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**Repository Test:**
```python
def test_get_by_email_found(db_session, seed_user_admin):
    repo = UserRepository(db_session)
    user = repo.get_by_email("admin@test.com")
    assert user is not None
    assert user.role == "admin"
```

---

## 📝 Notas Finais

**Princípios:**
1. **Qualidade > Quantidade** - Teste comportamento, não implementação
2. **Incremental** - Não tente 80% de uma vez
3. **Pragmático** - 100% nem sempre é necessário
4. **Sustentável** - Testes devem facilitar refatoração, não dificultar

**Meta realista para produção:** 75-80%  
**Meta ambiciosa:** 85%+  
**100%?** Apenas se fizer sentido (código crítico)

---

**Este plano é vivo - ajuste conforme necessidade do projeto!**

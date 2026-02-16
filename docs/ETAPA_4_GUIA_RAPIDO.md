# ETAPA 4 - RELATÓRIOS FINANCEIROS
**MVP Enterprise com Clean Architecture**  
**Data:** 2026-02-16  
**Versão:** 1.0.0  

---

## 📊 VISÃO GERAL

Módulo de **Relatórios Financeiros Profissionais** com 4 endpoints de inteligência de negócio:

1. **DRE** (Demonstração de

 Resultado) - Receitas, despesas e resultado
2. **Cashflow Diário** - Fluxo de caixa dia a dia
3. **Aging de Pendências** - Classificação por faixa de dias
4. **Top Lançamentos** - Maiores valores agregados

✅ Multi-tenant rigoroso  
✅ Validações de data  
✅ Série temporal completa (zeros preenchidos)  
✅ Performance otimizada (agregações SQL)  
✅ Clean Architecture mantida  

---

## 🏗️ ARQUITETURA

```
GET /reports/financial/*
    ↓
Router (report_routes.py)
    ↓ valida autenticação + multi-tenant
Service (report_service.py)
    ↓ valida datas + transforma dados
Repository (report_repository.py)
    ↓ queries SQL agregadas (GROUP BY, SUM)
Database (core.financial_entries)
```

**Camadas:**
- **Router:** HTTP, autenticação, query params
- **Service:** Validações, multi-tenant, transformações (preencher zeros)
- **Repository:** Queries SQL com agregações
- **Schemas:** Pydantic para request/response

---

## 📡 ENDPOINTS

### 1. GET /reports/financial/dre

**DRE Simplificada** - Demonstração de Resultado do Exercício

**Query Params:**
- `date_from` (date, obrigatório) - Data inicial YYYY-MM-DD
- `date_to` (date, obrigatório) - Data final YYYY-MM-DD
- `include_canceled` (bool, default=false) - Incluir cancelados

**Response 200:**
```json
{
  "period": {
    "date_from": "2026-01-01",
    "date_to": "2026-01-31"
  },
  "revenue_paid_total": 15000.00,
  "expense_paid_total": 8000.00,
  "net_paid": 7000.00,
  "revenue_pending_total": 3000.00,
  "expense_pending_total": 1500.00,
  "net_expected": 8500.00,
  "count_entries_total": 25
}
```

**Multi-tenant:**
- Admin: consolidado de todos usuários
- User: apenas seus lançamentos

**Validações:**
- date_from <= date_to
- Intervalo máximo: 366 dias

---

### 2. GET /reports/financial/cashflow/daily

**Fluxo de Caixa Diário** - Série temporal completa

**Query Params:**
- `date_from` (date, obrigatório)
- `date_to` (date, obrigatório)
- `include_canceled` (bool, default=false)

**Response 200:**
```json
{
  "period": {
    "date_from": "2026-02-01",
    "date_to": "2026-02-05"
  },
  "days": [
    {
      "date": "2026-02-01",
      "revenue_paid": 1000.00,
      "expense_paid": 500.00,
      "net_paid": 500.00,
      "revenue_pending": 200.00,
      "expense_pending": 0.00,
      "net_expected": 700.00
    },
    {
      "date": "2026-02-02",
      "revenue_paid": 0.00,
      "expense_paid": 0.00,
      "net_paid": 0.00,
      "revenue_pending": 0.00,
      "expense_pending": 0.00,
      "net_expected": 0.00
    }
  ]
}
```

**Observação:** Dias sem lançamentos aparecem com zero (série completa).

---

### 3. GET /reports/financial/pending/aging

**Aging de Pendências** - Classificação por faixa de dias

**Query Params:**
- `date_from` (date, obrigatório)
- `date_to` (date, obrigatório)
- `reference_date` (date, opcional, default=hoje)

**Response 200:**
```json
{
  "period": {
    "date_from": "2026-01-01",
    "date_to": "2026-02-16"
  },
  "reference_date": "2026-02-16",
  "pending_revenue": {
    "0_7_days": 1500.00,
    "8_30_days": 800.00,
    "31_plus_days": 200.00,
    "total": 2500.00
  },
  "pending_expense": {
    "0_7_days": 500.00,
    "8_30_days": 300.00,
    "31_plus_days": 100.00,
    "total": 900.00
  }
}
```

**Cálculo:** `days_old = reference_date - occurred_at`

**Faixas:**
- 0-7 dias
- 8-30 dias
- 31+ dias

---

### 4. GET /reports/financial/top

**Top Lançamentos** - Maiores valores agregados por descrição

**Query Params:**
- `kind` (string, obrigatório) - `revenue` ou `expense`
- `date_from` (date, obrigatório)
- `date_to` (date, obrigatório)
- `status` (string, default=`paid`) - `paid`, `pending`, `canceled`
- `limit` (int, default=10, max=50)

**Response 200:**
```json
{
  "period": {
    "date_from": "2026-01-01",
    "date_to": "2026-01-31"
  },
  "kind": "revenue",
  "status": "paid",
  "items": [
    {
      "description": "Venda Produto X",
      "total_amount": 5000.00,
      "count": 3,
      "last_occurred_at": "2026-01-28T10:30:00"
    },
    {
      "description": "Serviço Consultoria",
      "total_amount": 3500.00,
      "count": 1,
      "last_occurred_at": "2026-01-15T14:20:00"
    }
  ]
}
```

**Agregação:** Agrupa por `description`, soma `amount`, ordena por total DESC

---

## ✅ VALIDAÇÕES

| Validação | Regra | HTTP Status |
|-----------|-------|-------------|
| date_from <= date_to | Obrigatório | 400 |
| Intervalo máximo | 366 dias | 400 |
| kind válido | revenue OU expense | 400 |
| status válido | paid, pending, canceled | 400 |
| limit | 1-50 | Ajuste automático |

**Exemplos de erro 400:**
```json
{
  "detail": "date_from (20026-02-01) não pode ser maior que date_to (2026-01-01)"
}
```

```json
{
  "detail": "Intervalo muito grande: 380 dias. Máximo permitido: 366 dias"
}
```

---

## 🔐 MULTI-TENANT

Todos os relatórios respeitam multi-tenant:

| Role | Filtro | Visualização |
|------|--------|--------------|
| **admin** | `user_id = None` | Todos usuários (consolidado) |
| **user, technician, finance** | `user_id = current_user.id` | Apenas próprios lançamentos |

**Implementação:**
```python
user_id_filter = None if current_user.role == "admin" else current_user.id
```

---

## 🎯 REGRAS DE NEGÓCIO

### DRE
- **Receitas pagas:** `kind=revenue AND status=paid`
- **Despesas pagas:** `kind=expense AND status=paid`
- **Net paid:** `revenue_paid - expense_paid`
- **Net expected:** `(revenue_paid + revenue_pending) - (expense_paid + expense_pending)`

### Cashflow Diário
- **Preenche zeros:** Dias sem lançamentos = 0.00
- **Agregação:** Por `occurred_at::date`
- **Ordenação:** Cronológica (date ASC)

### Aging
- **Apenas pending:** `status=pending`
- **Cálculo:** `reference_date - occurred_at` (em dias)
- **Classificação automática:** 0-7, 8-30, 31+

### Top Entries
- **Agregação:** GROUP BY description
- **Ordenação:** SUM(amount) DESC
- **Limit:** 1-50 (default 10)

---

## 🚀 INSTALAÇÃO

**Nenhum script SQL adicional necessário!**

Módulo de relatórios usa apenas `core.financial_entries` (já existe da ETAPA 3A).

**Índices existentes** são suficientes:
- `idx_user_occurred` (user_id + occurred_at) ✅ DRE, Cashflow, Aging
- `idx_status` (status) ✅ Filtros por status
- `idx_kind` (kind) ✅ Filtros por kind

**Nenhuma alteração de banco necessária.** 🎉

---

## 📝 QUICKSTART

### 1. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@jsp.com&password=123456"
```

Resposta:
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}
```

### 2. DRE do mês atual
```bash
curl -X GET "http://localhost:8000/reports/financial/dre?date_from=2026-02-01&date_to=2026-02-28" \
  -H "Authorization: Bearer <TOKEN>"
```

### 3. Cashflow últimos 7 dias
```bash
curl -X GET "http://localhost:8000/reports/financial/cashflow/daily?date_from=2026-02-09&date_to=2026-02-16" \
  -H "Authorization: Bearer <TOKEN>"
```

### 4. Aging de pendências
```bash
curl -X GET "http://localhost:8000/reports/financial/pending/aging?date_from=2026-01-01&date_to=2026-02-16" \
  -H "Authorization: Bearer <TOKEN>"
```

### 5. Top 5 receitas pagas do mês
```bash
curl -X GET "http://localhost:8000/reports/financial/top?kind=revenue&status=paid&date_from=2026-02-01&date_to=2026-02-28&limit=5" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 📊 PERFORMANCE

### Queries Otimizadas

Todas as queries usam:
- ✅ `func.sum()` - Agregação no banco
- ✅ `func.count()` - Contagem no banco
- ✅ `GROUP BY` - Agrupamento eficiente
- ✅ `cast(occurred_at, Date)` - Índices aproveitados
- ✅ Filtros `WHERE` antes de agregações

### Índices Utilizados

| Endpoint | Índice Principal | Benefício |
|----------|------------------|-----------|
| DRE | `idx_user_occurred` | Multi-tenant + período |
| Cashflow | `idx_user_occurred` | GROUP BY date eficiente |
| Aging | `idx_status` + `idx_user_occurred` | Filtro pending rápido |
| Top | `idx_kind` + `idx_status` | Filtros combinados |

### Limites de Proteção

| Proteção | Valor | Finalidade |
|----------|-------|------------|
| Intervalo máximo | 366 dias | Evitar queries pesadas |
| Top limit | 50 | Limitar resultado |
| Paginação DRE | N/A | Agregado único |

---

## 🛡️ SEGURANÇA

### Autenticação
- ✅ Todos endpoints exigem Bearer token
- ✅ Token validado via `get_current_user`

### Multi-Tenant Enforcement
- ✅ Admin vê consolidado
- ✅ Users veem apenas seus dados
- ✅ Filtro aplicado no Repository

### Sanitização de Erros
- ✅ Produção: erros genéricos
- ✅ Dev: stack trace completo
- ✅ Validações: mensagens claras (400)

---

## 📁 ARQUIVOS CRIADOS

| # | Arquivo | Linhas | Função |
|---|---------|--------|--------|
| 1 | `app/repositories/report_repository.py` | ~450 | Queries SQL agregadas |
| 2 | `app/services/report_service.py` | ~280 | Validações + transformações |
| 3 | `app/routers/report_routes.py` | ~300 | Endpoints HTTP |
| 4 | `app/schemas/report_schema.py` | ~200 | Models Pydantic |
| 5 | `app/main.py` (modificado) | +2 | Registro do router |

**Total:** ~1.230 linhas de código (sem contar documentação)

---

## 🧪 TESTES

Veja comandos executáveis em:
- **[COMANDOS_TESTE_ETAPA4.md](COMANDOS_TESTE_ETAPA4.md)** - PowerShell + Bash

**Cobertura de testes:**
1. Login admin e user
2. Criar lançamentos (paid, pending, revenue, expense)
3. DRE com valores corretos
4. Cashflow com zeros preenchidos
5. Aging classificado em faixas
6. Top revenue ordenado
7. Multi-tenant isolado
8. Admin vê consolidado

---

## 📜 LICENÇA

Parte do projeto JSP ERP Training  
Uso educacional e comercial permitido  

---

**Documentação criada em:** 2026-02-16  
**Autor:** GitHub Copilot (Claude Sonnet 4.5)  
**Versão:** ETAPA 4 v1.0.0

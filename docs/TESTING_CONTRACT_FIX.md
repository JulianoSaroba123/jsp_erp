# 🧪 GUIA DE TESTES - CORREÇÃO DE CONTRATOS DASHBOARD

## ✅ ARQUIVOS ALTERADOS

### 1. Contratos Centralizados (NOVO)
- ✅ `frontend/src/contracts/report.contract.ts` (CRIADO)

### 2. API Client
- ✅ `frontend/src/api/reports.ts` (ATUALIZADO)
  - Remove interfaces duplicadas
  - Importa de `contracts/report.contract.ts`

### 3. Dashboard
- ✅ `frontend/src/pages/Dashboard.tsx` (ATUALIZADO)
  - Usa `revenue_paid_total` em vez de `revenues_paid`
  - Usa `expense_paid_total` em vez de `expenses_paid`
  - Usa `net_paid` em vez de `net_result_paid`
  - Adiciona fallbacks seguros (`?? 0`)
  - Importa tipo `DREData` do contrato

### 4. Documentação (NOVO)
- ✅ `docs/CONTRACT_PATTERN.md` (CRIADO)

---

## 📊 DIFF RESUMIDO

### Dashboard.tsx

```diff
  import { useQuery } from '@tanstack/react-query';
  import { Link } from 'react-router-dom';
  import { getOrders } from '../api/orders';
  import { getDRE } from '../api/reports';
  import { formatCurrencyBRL, formatDateBR, formatDateISO } from '../lib/format';
+ import type { DREData } from '../contracts/report.contract';

  export function Dashboard() {
    // ...
    
-   const { data: dreData, isLoading: dreLoading, isError: dreError } = useQuery({
+   const { data: dreData, isLoading: dreLoading, isError: dreError } = useQuery<DREData>({
      queryKey: ['dre', dateFrom, dateTo],
      queryFn: () => getDRE({ date_from: dateFrom, date_to: dateTo }),
    });

+   // ⚠️ IMPORTANTE: Usar nomes EXATAMENTE como retornado pelo backend
+   // Backend: revenue_paid_total, expense_paid_total, net_paid
+   // Fallback seguro: ?? 0 (nunca undefined/NaN)
    const totalOrders = ordersData?.total || 0;
-   const totalRevenue = dreData?.revenues_paid || 0;
-   const totalExpenses = dreData?.expenses_paid || 0;
-   const netResult = dreData?.net_result_paid || 0;
+   const totalRevenue = dreData?.revenue_paid_total ?? 0;
+   const totalExpenses = dreData?.expense_paid_total ?? 0;
+   const netResult = dreData?.net_paid ?? 0;
```

### api/reports.ts

```diff
  import { apiClient } from './client';
+ import {
+   DREData,
+   CashflowDailyData,
+   AgingData,
+   TopEntriesData,
+ } from '../contracts/report.contract';

- // ============================================================================
- // Types - Reports API
- // ============================================================================
- 
- export interface DREData {
-   revenues_paid: number;
-   revenues_pending: number;
-   expenses_paid: number;
-   expenses_pending: number;
-   net_result_paid: number;
-   net_result_expected: number;
-   total_entries: number;
- }
- 
- export interface CashflowDay { ... }
- export interface CashflowDailyData { ... }
- export interface AgingBucket { ... }
- export interface AgingData { ... }
- export interface TopEntry { ... }
- export interface TopEntriesData { ... }

+ // ============================================================================
+ // API Functions - Reports
+ // ============================================================================
+ // Contratos centralizados em: frontend/src/contracts/report.contract.ts
+ // ============================================================================
```

---

## 🧪 COMO TESTAR

### Pré-requisitos
- Backend rodando: `http://localhost:8000`
- Frontend rodando: `http://localhost:5174`
- Banco de dados com lançamentos financeiros

---

### TESTE 1: Dashboard exibe KPIs corretamente

#### Passo 1: Inicie o frontend
```powershell
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\frontend"
npm run dev
```

#### Passo 2: Acesse o Dashboard
- Abra navegador em: `http://localhost:5174/dashboard`
- Faça login (usuário: admin / senha: admin123 ou seu usuário)

#### Passo 3: Verifique os Cards
Devem aparecer **valores reais** (não undefined/NaN/0 incorreto):

```
┌─────────────────────────────────────────────────────┐
│ 📦 Total de Pedidos          │ 💰 Receitas (Pagas)  │
│ 15                           │ R$ 25.000,00         │
│                              │                      │
│ 📉 Despesas (Pagas)          │ 📈 Resultado Líquido │
│ R$ 8.500,00                  │ R$ 16.500,00         │
└─────────────────────────────────────────────────────┘
```

✅ **Sucesso se:**
- Valores aparecem corretamente
- Não há `R$ NaN`
- Não há `R$ undefined`
- Não há `R$ 0,00` quando deveria haver valores

❌ **Falha se:**
- Cards mostram `R$ 0,00` mas há lançamentos no banco
- Aparecer `undefined` ou `NaN`
- Console do navegador mostra erros

---

### TESTE 2: Network Request está correto

#### Passo 1: Abra DevTools
- Pressione `F12` no navegador
- Vá para a aba **Network**

#### Passo 2: Recarregue o Dashboard
- Pressione `Ctrl+R`

#### Passo 3: Verifique a requisição DRE
- Procure por: `GET /reports/financial/dre?date_from=...&date_to=...`
- Clique na requisição
- Vá para a aba **Preview** ou **Response**

#### Passo 4: Verifique a resposta JSON
```json
{
  "period": {
    "date_from": "2026-04-08",
    "date_to": "2026-05-08"
  },
  "revenue_paid_total": 25000.0,
  "expense_paid_total": 8500.0,
  "net_paid": 16500.0,
  "revenue_pending_total": 5000.0,
  "expense_pending_total": 2000.0,
  "net_expected": 19500.0,
  "count_entries_total": 42
}
```

✅ **Sucesso se:**
- Status: `200 OK`
- JSON contém `revenue_paid_total` (não `revenues_paid`)
- JSON contém `expense_paid_total` (não `expenses_paid`)
- JSON contém `net_paid` (não `net_result_paid`)

---

### TESTE 3: TypeScript não tem erros

```powershell
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\frontend"

# Se houver script de type check:
npm run type-check

# OU verificar durante build:
npm run build
```

✅ **Sucesso se:**
- Sem erros de tipo
- Build completa com sucesso

---

### TESTE 4: Console do navegador limpo

#### Passo 1: Abra DevTools
- Pressione `F12`
- Vá para a aba **Console**

#### Passo 2: Recarregue o Dashboard

✅ **Sucesso se:**
- Sem erros vermelhos
- Sem warnings sobre propriedades undefined

❌ **Falha se:**
- Aparecer: `Cannot read property 'revenues_paid' of undefined`
- Aparecer: `Cannot read property 'expenses_paid' of undefined`

---

### TESTE 5: Outros módulos não foram afetados

#### Navegue para:
- `/orders` - Pedidos
- `/financial` - Financeiro
- `/products` - Produtos
- `/customers` - Clientes

✅ **Sucesso se:**
- Todas as páginas funcionam normalmente
- Nenhum módulo foi quebrado

---

## 🔍 VALIDAÇÃO TÉCNICA

### Verificar contratos estão sincronizados

```powershell
# Backend
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"
cat app/schemas/report_schema.py | grep "revenue_paid_total\|expense_paid_total\|net_paid"

# Frontend
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\frontend"
cat src/contracts/report.contract.ts | grep "revenue_paid_total\|expense_paid_total\|net_paid"
```

Ambos devem ter os mesmos nomes.

---

### Verificar que nomes antigos não existem mais

```powershell
cd "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\frontend"

# Buscar nomes antigos (não deve retornar resultados no código):
grep -r "revenues_paid" src/ --include="*.ts" --include="*.tsx"
grep -r "expenses_paid" src/ --include="*.ts" --include="*.tsx"
grep -r "net_result_paid" src/ --include="*.ts" --include="*.tsx"
```

✅ **Sucesso se:**
- Nenhum resultado (ou apenas em comentários)

---

## 🐛 TROUBLESHOOTING

### Problema: Dashboard mostra R$ 0,00 em todos os cards

**Causa:** Backend não está retornando dados ou usuário não tem lançamentos

**Solução:**
1. Verifique se backend está rodando: `http://localhost:8000/docs`
2. Acesse `/financial` e crie alguns lançamentos
3. Recarregue o Dashboard

---

### Problema: Aparecer erro de TypeScript

**Causa:** Cache do TypeScript desatualizado

**Solução:**
```powershell
cd frontend
# Limpar cache
rm -rf node_modules/.vite
rm -rf dist
# Reiniciar dev server
npm run dev
```

---

### Problema: "Cannot read property of undefined"

**Causa:** Frontend ainda tentando acessar nomes antigos

**Solução:**
1. Verificar se salvou todos os arquivos
2. Reiniciar dev server (Ctrl+C e `npm run dev` novamente)
3. Limpar cache do navegador (Ctrl+Shift+Delete)

---

## ✅ CHECKLIST FINAL

Antes de dar como concluído, verificar:

- [ ] Dashboard exibe valores corretos (não R$ 0,00 incorreto)
- [ ] Network request retorna JSON com nomes corretos
- [ ] Console do navegador sem erros
- [ ] TypeScript sem erros de compilação
- [ ] Outros módulos (Orders, Financial) ainda funcionam
- [ ] Nomes antigos removidos do código
- [ ] Documentação criada em `docs/CONTRACT_PATTERN.md`
- [ ] Contratos centralizados em `frontend/src/contracts/`

---

## 🎯 CRITÉRIO DE ACEITE

A correção está completa quando:

1. ✅ Dashboard mostra KPIs financeiros corretamente
2. ✅ Frontend usa os mesmos nomes do backend (`revenue_paid_total`, etc)
3. ✅ Contratos estão centralizados em `src/contracts/`
4. ✅ Sem bug silencioso (undefined/NaN)
5. ✅ Base pronta para próximos módulos (Products, Customers, Reports)
6. ✅ Documentação disponível para equipe

---

## 📚 REFERÊNCIAS

- Contratos: `frontend/src/contracts/report.contract.ts`
- Documentação: `docs/CONTRACT_PATTERN.md`
- Schema Backend: `backend/app/schemas/report_schema.py`
- Dashboard: `frontend/src/pages/Dashboard.tsx`

# 📋 PADRÃO OFICIAL DE CONTRATOS - ERP JSP

## 🎯 OBJETIVO

Estabelecer um padrão único e consistente para contratos entre Backend (FastAPI + Pydantic) e Frontend (React + TypeScript), eliminando bugs silenciosos causados por inconsistências de nomenclatura.

---

## 📐 PRINCÍPIOS FUNDAMENTAIS

### 1. **Backend é a fonte oficial de contratos**

- O backend (FastAPI + Pydantic) define a **FONTE OFICIAL** dos contratos
- Schemas Pydantic em `backend/app/schemas/` são a referência definitiva
- Frontend deve **REPLICAR EXATAMENTE** os nomes dos campos

### 2. **Nunca criar aliases arbitrários**

❌ **ERRADO:**
```typescript
// Backend retorna: revenue_paid_total
// Frontend cria alias diferente:
interface DREData {
  revenues_paid: number;  // ❌ ERRADO! Nome diferente
}
```

✅ **CORRETO:**
```typescript
// Backend retorna: revenue_paid_total
// Frontend usa o mesmo nome:
interface DREData {
  revenue_paid_total: number;  // ✅ CORRETO! Nome idêntico
}
```

### 3. **Sempre usar snake_case**

- FastAPI/Pydantic retorna campos em `snake_case` por padrão
- **NUNCA** converter para camelCase no frontend
- Manter consistência com a API REST

❌ **ERRADO:**
```typescript
interface DREData {
  revenuePaidTotal: number;  // ❌ camelCase - errado!
}
```

✅ **CORRETO:**
```typescript
interface DREData {
  revenue_paid_total: number;  // ✅ snake_case - correto!
}
```

### 4. **Contratos devem ser centralizados**

- Todos os contratos TypeScript devem ficar em `frontend/src/contracts/`
- **Single Source of Truth** no frontend
- Facilita manutenção e evita duplicação

---

## 📂 ESTRUTURA DE CONTRATOS

```
frontend/src/
├── contracts/
│   ├── report.contract.ts        # Contratos de relatórios
│   ├── order.contract.ts         # Contratos de pedidos (futuro)
│   ├── financial.contract.ts     # Contratos financeiros (futuro)
│   ├── customer.contract.ts      # Contratos de clientes (futuro)
│   └── product.contract.ts       # Contratos de produtos (futuro)
│
├── api/
│   ├── reports.ts                # Import de contracts/report.contract.ts
│   ├── orders.ts                 # Import de contracts/order.contract.ts
│   └── ...
│
└── pages/
    ├── Dashboard.tsx             # Import de contracts/report.contract.ts
    └── ...
```

---

## 📝 TEMPLATE DE CONTRATO

### Backend (Source of Truth)

```python
# backend/app/schemas/report_schema.py

from pydantic import BaseModel, Field

class DREResponse(BaseModel):
    """Resposta do endpoint DRE."""
    revenue_paid_total: float = Field(..., description="Total de receitas pagas")
    expense_paid_total: float = Field(..., description="Total de despesas pagas")
    net_paid: float = Field(..., description="Resultado líquido pago")
```

### Frontend (Replicação Exata)

```typescript
// frontend/src/contracts/report.contract.ts

/**
 * CONTRACT: Reports API
 * Source of Truth: backend/app/schemas/report_schema.py
 * 
 * IMPORTANTE: Usar EXATAMENTE os mesmos nomes do backend
 */

/**
 * Resposta do endpoint GET /reports/financial/dre
 * Corresponde a: DREResponse (backend/app/schemas/report_schema.py)
 */
export interface DREData {
  revenue_paid_total: number;  // ✅ Exatamente como no backend
  expense_paid_total: number;  // ✅ Exatamente como no backend
  net_paid: number;            // ✅ Exatamente como no backend
}
```

---

## 🔄 WORKFLOW DE CRIAÇÃO DE CONTRATOS

### Passo 1: Backend define o contrato (Pydantic)

```python
# backend/app/schemas/customer_schema.py

class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: str | None
    cpf_cnpj: str | None
    created_at: datetime
```

### Passo 2: Frontend replica o contrato (TypeScript)

```typescript
// frontend/src/contracts/customer.contract.ts

/**
 * Resposta do endpoint GET /customers/{id}
 * Corresponde a: CustomerResponse (backend/app/schemas/customer_schema.py)
 */
export interface Customer {
  id: string;
  name: string;
  email: string | null;
  cpf_cnpj: string | null;
  created_at: string;  // ISO datetime string
}
```

### Passo 3: API client usa o contrato

```typescript
// frontend/src/api/customers.ts

import { Customer } from '../contracts/customer.contract';
import { apiClient } from './client';

export async function getCustomer(id: string): Promise<Customer> {
  const response = await apiClient.get<Customer>(`/customers/${id}`);
  return response.data;
}
```

### Passo 4: Componente usa o contrato

```typescript
// frontend/src/pages/Customers/CustomerDetail.tsx

import type { Customer } from '../../contracts/customer.contract';

function CustomerDetail({ id }: { id: string }) {
  const { data } = useQuery<Customer>({
    queryKey: ['customer', id],
    queryFn: () => getCustomer(id),
  });
  
  // ✅ TypeScript garante que campos existem
  return <div>{data?.name}</div>;
}
```

---

## 🛡️ HARDENING OBRIGATÓRIO

### 1. **Sempre usar fallback seguro**

❌ **ERRADO:**
```typescript
const totalRevenue = dreData.revenue_paid_total;  // ❌ Pode ser undefined
```

✅ **CORRETO:**
```typescript
const totalRevenue = dreData?.revenue_paid_total ?? 0;  // ✅ Nunca undefined/NaN
```

### 2. **Validar tipos em componentes**

```typescript
const { data: dreData, isLoading, isError } = useQuery<DREData>({
  //                                                     ^^^^^^^^ Tipo explícito
  queryKey: ['dre'],
  queryFn: getDRE,
});
```

### 3. **Documentar correspondência Backend ↔ Frontend**

```typescript
/**
 * Resposta do endpoint GET /reports/financial/dre
 * Corresponde a: DREResponse (backend/app/schemas/report_schema.py)
 * 
 * ⚠️ ATENÇÃO: Usar EXATAMENTE os nomes do backend
 */
export interface DREData {
  revenue_paid_total: number;  // Corresponde a: revenue_paid_total (Pydantic)
  // ...
}
```

---

## ❌ ANTI-PATTERNS (O QUE NUNCA FAZER)

### 1. **Criar adapters desnecessários**

❌ **ERRADO:**
```typescript
// Adapter desnecessário que cria inconsistência
function adaptDREResponse(backend: BackendDRE): FrontendDRE {
  return {
    revenuesPaid: backend.revenue_paid_total,  // ❌ Criando alias arbitrário
    expensesPaid: backend.expense_paid_total,
  };
}
```

✅ **CORRETO:**
```typescript
// Usar o contrato direto, sem adapter
const dreData: DREData = await getDRE(params);
```

### 2. **Duplicar contratos em múltiplos arquivos**

❌ **ERRADO:**
```typescript
// api/reports.ts
export interface DREData { ... }

// pages/Dashboard.tsx
export interface DREData { ... }  // ❌ Duplicação!
```

✅ **CORRETO:**
```typescript
// contracts/report.contract.ts (SINGLE SOURCE)
export interface DREData { ... }

// api/reports.ts
import { DREData } from '../contracts/report.contract';

// pages/Dashboard.tsx
import type { DREData } from '../../contracts/report.contract';
```

### 3. **Misturar camelCase e snake_case**

❌ **ERRADO:**
```typescript
interface Customer {
  id: string;              // ✅ snake_case
  firstName: string;        // ❌ camelCase - inconsistente!
  last_name: string;        // ✅ snake_case
  phoneNumber: string;      // ❌ camelCase - inconsistente!
}
```

✅ **CORRETO:**
```typescript
interface Customer {
  id: string;              // ✅ snake_case
  first_name: string;      // ✅ snake_case
  last_name: string;       // ✅ snake_case
  phone_number: string;    // ✅ snake_case
}
```

---

## 🔍 CHECKLIST DE VALIDAÇÃO

Ao criar ou atualizar um contrato, verifique:

- [ ] Contrato TypeScript está em `frontend/src/contracts/`
- [ ] Nomes dos campos são **EXATAMENTE** iguais ao backend (Pydantic)
- [ ] Todos os campos estão usando `snake_case`
- [ ] Tipos TypeScript correspondem aos tipos Python:
  - `str` → `string`
  - `int` → `number`
  - `float` → `number`
  - `UUID` → `string`
  - `datetime` → `string` (ISO format)
  - `bool` → `boolean`
  - `list[T]` → `T[]`
  - `Optional[T]` → `T | null`
- [ ] Documentação indica qual schema Pydantic corresponde
- [ ] API client importa de `contracts/`
- [ ] Componentes importam de `contracts/`
- [ ] Fallbacks seguros (`??`) em todos os acessos opcionais

---

## 🚀 MIGRAÇÃO DE CONTRATOS EXISTENTES

Para migrar contratos já existentes:

1. **Identificar contrato no backend**: Localizar schema Pydantic
2. **Criar arquivo em contracts/**: `frontend/src/contracts/{modulo}.contract.ts`
3. **Replicar nomes exatos**: Copiar campos mantendo nomenclatura
4. **Atualizar imports**: Substituir imports antigos por `contracts/`
5. **Corrigir referências**: Atualizar todos os locais que usam os tipos
6. **Validar**: Testar que dados são exibidos corretamente

---

## 📚 EXEMPLOS PRÁTICOS

### Exemplo 1: Relatórios (DRE)

**Backend:**
```python
# backend/app/schemas/report_schema.py
class DREResponse(BaseModel):
    revenue_paid_total: float
    expense_paid_total: float
    net_paid: float
```

**Frontend:**
```typescript
// frontend/src/contracts/report.contract.ts
export interface DREData {
  revenue_paid_total: number;
  expense_paid_total: number;
  net_paid: number;
}
```

**Uso:**
```typescript
// frontend/src/pages/Dashboard.tsx
import type { DREData } from '../contracts/report.contract';

const totalRevenue = dreData?.revenue_paid_total ?? 0;  // ✅ Correto
```

---

## 🏆 BENEFÍCIOS DO PADRÃO

1. ✅ **Elimina bugs silenciosos** (undefined/NaN)
2. ✅ **TypeScript detecta erros de tipo** em tempo de desenvolvimento
3. ✅ **Single Source of Truth** facilita manutenção
4. ✅ **Onboarding mais rápido** (desenvolvedores sabem onde procurar)
5. ✅ **Refactoring seguro** (TypeScript alerta sobre quebras)
6. ✅ **Consistência** entre todos os módulos

---

## 📞 CONTATO E DÚVIDAS

Para dúvidas sobre o padrão de contratos:
- Verificar este documento: `docs/CONTRACT_PATTERN.md`
- Consultar exemplos em: `frontend/src/contracts/report.contract.ts`
- Verificar schemas backend em: `backend/app/schemas/`

**Lembre-se: Backend é SEMPRE a fonte oficial de contratos!**

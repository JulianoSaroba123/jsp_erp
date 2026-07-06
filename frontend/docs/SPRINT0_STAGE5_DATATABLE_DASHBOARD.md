# Sprint 0 - Etapa 5

## Objetivo
Criar fundacao reutilizavel de DataTable Enterprise e blocos estruturais de Dashboard sem logica de negocio real e sem consumo de endpoints.

## DataTable Enterprise
Arquivo base:
- src/components/table/DataTableEnterprise.tsx

Recursos incluidos:
- columns e data tipados por generics
- loading, empty state e error state
- busca visual local
- ordenacao visual local
- paginacao visual local
- slots de toolbar e actions
- renderRowActions por linha
- estrutura de coluna inspirada em adocao futura com TanStack Table

Exemplo minimo:

```tsx
import { DataTableEnterprise, type DataTableColumn } from '../components/table';

type Row = { id: string; name: string; status: string };

const columns: Array<DataTableColumn<Row>> = [
  { id: 'name', header: 'Nome', accessorKey: 'name', sortable: true },
  { id: 'status', header: 'Status', accessorKey: 'status', sortable: true },
];

<DataTableEnterprise
  title="Tabela Base"
  columns={columns}
  data={rows}
  loading={false}
  error={null}
/>
```

## Dashboard Foundation
Arquivos base:
- src/components/dashboard/DashboardGrid.tsx
- src/components/dashboard/DashboardWidget.tsx
- src/components/dashboard/KpiWidget.tsx
- src/components/dashboard/ChartWidgetPlaceholder.tsx
- src/components/dashboard/ActivityListPlaceholder.tsx

Recursos incluidos:
- grid responsivo reutilizavel
- widget base com loading/error
- KPI widget para metricas visuais
- placeholder de grafico
- placeholder de lista de atividades

Exemplo minimo:

```tsx
import {
  DashboardGrid,
  KpiWidget,
  ChartWidgetPlaceholder,
  ActivityListPlaceholder,
} from '../components/dashboard';

<DashboardGrid columns={3}>
  <KpiWidget title="Receita" value="R$ 0,00" trend="0%" />
  <ChartWidgetPlaceholder title="Evolucao" />
  <ActivityListPlaceholder />
</DashboardGrid>
```

## Limites da Etapa 5
- sem consumo real de API
- sem dashboard funcional
- sem alteracao de telas de negocio

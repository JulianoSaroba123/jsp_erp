/**
 * CONTRACT: Reports API
 * 
 * IMPORTANTE: Este contrato deve ser SEMPRE sincronizado com o backend.
 * Source of Truth: backend/app/schemas/report_schema.py
 * 
 * REGRAS:
 * - Backend é a fonte oficial dos contratos
 * - Frontend deve replicar nomes EXATAMENTE como no backend
 * - NUNCA criar aliases arbitrários (revenues_paid → revenue_paid_total)
 * - NUNCA usar camelCase para nomes de campos da API
 * - Sempre usar snake_case conforme retornado pelo FastAPI/Pydantic
 */

// ============================================================================
// DRE (Demonstração de Resultado do Exercício)
// ============================================================================

/**
 * Período do relatório DRE
 * Corresponde a: DREPeriod (backend)
 */
export interface DREPeriod {
  date_from: string; // ISO date format: YYYY-MM-DD
  date_to: string;   // ISO date format: YYYY-MM-DD
}

/**
 * Resposta do endpoint GET /reports/financial/dre
 * Corresponde a: DREResponse (backend/app/schemas/report_schema.py)
 * 
 * ⚠️ ATENÇÃO: Usar EXATAMENTE os nomes do backend
 */
export interface DREData {
  period: DREPeriod;
  
  // Valores pagos
  revenue_paid_total: number;   // Total de receitas pagas
  expense_paid_total: number;   // Total de despesas pagas
  net_paid: number;             // Resultado líquido pago (receitas - despesas)
  
  // Valores pendentes
  revenue_pending_total: number;  // Total de receitas pendentes
  expense_pending_total: number;  // Total de despesas pendentes
  net_expected: number;           // Resultado esperado (pago + pendente)
  
  // Metadados
  count_entries_total: number;    // Total de lançamentos no período
}

// ============================================================================
// Cashflow Diário
// ============================================================================

/**
 * Item de fluxo de caixa de um dia
 * Corresponde a: CashflowDailyItem (backend)
 */
export interface CashflowDailyItem {
  date: string; // ISO date format: YYYY-MM-DD
  revenue_paid: number;
  expense_paid: number;
  net_paid: number;
  revenue_pending: number;
  expense_pending: number;
  net_expected: number;
}

/**
 * Resposta do endpoint GET /reports/financial/cashflow/daily
 * Corresponde a: CashflowDailyResponse (backend)
 */
export interface CashflowDailyData {
  period: DREPeriod;
  days: CashflowDailyItem[];
}

// ============================================================================
// Aging de Pendências
// ============================================================================

/**
 * Faixa de aging (0-7, 8-30, 31+)
 * Corresponde a: AgingBucket (backend)
 */
export interface AgingBucket {
  days_0_7: number;      // Pendências de 0 a 7 dias
  days_8_30: number;     // Pendências de 8 a 30 dias
  days_31_plus: number;  // Pendências acima de 31 dias
  total: number;         // Total de pendências
}

/**
 * Resposta do endpoint GET /reports/financial/pending/aging
 * Corresponde a: AgingResponse (backend)
 */
export interface AgingData {
  period: DREPeriod;
  reference_date: string; // ISO date format: YYYY-MM-DD
  pending_revenue: AgingBucket;
  pending_expense: AgingBucket;
}

// ============================================================================
// Top Lançamentos
// ============================================================================

/**
 * Entry do top lançamentos
 * Corresponde a: TopEntry (backend)
 */
export interface TopEntry {
  description: string;
  total_amount: number;
  count: number;
}

/**
 * Resposta do endpoint GET /reports/financial/top
 * Corresponde a: TopEntriesResponse (backend)
 */
export interface TopEntriesData {
  period: DREPeriod;
  kind: string;
  status: string;
  entries: TopEntry[];
}

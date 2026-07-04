import { apiClient } from './client';

// ============================================================================
// Types - Reports API
// ============================================================================


export interface DREData {
  revenues_paid: number;
  revenues_pending: number;
  expenses_paid: number;
  expenses_pending: number;
  net_result_paid: number;
  net_result_expected: number;
  total_entries: number;
}

export interface CashflowDay {
  date: string;
  revenues_paid: number;
  revenues_pending: number;
  expenses_paid: number;
  expenses_pending: number;
  net_paid: number;
  net_expected: number;
}

export interface CashflowDailyData {
  days: CashflowDay[];
  summary: {
    total_revenues_paid: number;
    total_expenses_paid: number;
    total_net_paid: number;
  };
}

export interface AgingBucket {
  range: string;
  count: number;
  total_amount: number;
}

export interface AgingData {
  buckets: AgingBucket[];
  total_pending: number;
  total_amount_pending: number;
}

export interface TopEntry {
  description: string;
  total_amount: number;
  count: number;
}

export interface TopEntriesData {
  kind: string;
  status: string;
  entries: TopEntry[];
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * GET /reports/financial/dre
 * Busca DRE (Demonstração de Resultado do Exercício)
 */
export async function getDRE(params: {
  date_from: string; // YYYY-MM-DD
  date_to: string;   // YYYY-MM-DD
  include_canceled?: boolean;
}): Promise<DREData> {
  const response = await apiClient.get<DREData>('/reports/financial/dre', { params });
  return response.data;
}

/**
 * GET /reports/financial/cashflow/daily
 * Busca fluxo de caixa diário (série temporal)
 */
export async function getCashflowDaily(params: {
  date_from: string;
  date_to: string;
  include_canceled?: boolean;
}): Promise<CashflowDailyData> {
  const response = await apiClient.get<CashflowDailyData>('/reports/financial/cashflow/daily', { params });
  return response.data;
}

/**
 * GET /reports/financial/pending/aging
 * Busca aging de pendências (classificação por faixa de dias)
 */
export async function getAgingPending(params: {
  date_from: string;
  date_to: string;
  reference_date?: string;
}): Promise<AgingData> {
  const response = await apiClient.get<AgingData>('/reports/financial/pending/aging', { params });
  return response.data;
}

/**
 * GET /reports/financial/top
 * Busca top lançamentos por valor (agregados por descrição)
 */
export async function getTopEntries(params: {
  kind: 'revenue' | 'expense';
  date_from: string;
  date_to: string;
  status?: 'paid' | 'pending' | 'canceled';
  limit?: number;
}): Promise<TopEntriesData> {
  const response = await apiClient.get<TopEntriesData>('/reports/financial/top', { params });
  return response.data;
}

import { apiClient } from './client';

// ============================================================================
// Types - Financial API
// ============================================================================

export interface FinancialEntry {
  id: string;
  user_id: string;
  order_id: string | null;
  kind: 'revenue' | 'expense';
  status: 'pending' | 'paid' | 'canceled';
  amount: number;
  description: string;
  category?: string | null;
  subcategory?: string | null;
  due_date?: string | null;
  payment_date?: string | null;
  document_number?: string | null;
  document_type?: string | null;
  payment_method?: string | null;
  notes?: string | null;
  original_amount?: number | null;
  interest?: number | null;
  discount?: number | null;
  penalty?: number | null;
  origin?: string | null;
  is_recurring?: boolean | null;
  recurrence_frequency?: string | null;
  occurred_at: string;
  created_at: string;
  updated_at: string | null;
}

export interface FinancialListResponse {
  items: FinancialEntry[];
  page: number;
  page_size: number;
  total: number;
}

export interface CreateFinancialData {
  kind: 'revenue' | 'expense';
  amount: number;
  description: string;
  occurred_at?: string; // ISO datetime, opcional (backend usa now se não enviar)
}

export interface UpdateFinancialStatusData {
  status: 'pending' | 'paid' | 'canceled';
}

// ============================================================================
// Query Params
// ============================================================================

export interface GetFinancialEntriesParams {
  page: number;
  page_size: number;
  kind?: 'revenue' | 'expense';
  status?: 'pending' | 'paid' | 'canceled';
  date_from?: string; // ISO datetime
  date_to?: string;   // ISO datetime
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * GET /financial/entries
 * Lista lançamentos financeiros com paginação e filtros
 */
export async function getFinancialEntries(params: GetFinancialEntriesParams): Promise<FinancialListResponse> {
  const response = await apiClient.get<FinancialListResponse>('/financial/entries', { params });
  return response.data;
}

/**
 * POST /financial/entries
 * Cria novo lançamento financeiro manual
 */
export async function createFinancialEntry(data: CreateFinancialData): Promise<FinancialEntry> {
  const response = await apiClient.post<FinancialEntry>('/financial/entries', data);
  return response.data;
}

/**
 * PATCH /financial/entries/{id}/status
 * Atualiza APENAS o status de um lançamento
 * (Backend não permite edição completa de description/amount/kind)
 */
export async function updateFinancialStatus(
  id: string,
  data: UpdateFinancialStatusData
): Promise<FinancialEntry> {
  const response = await apiClient.patch<FinancialEntry>(`/financial/entries/${id}/status`, data);
  return response.data;
}

/**
 * DELETE /financial/entries/{id}
 * Exclui um lançamento financeiro
 */
export async function deleteFinancialEntry(id: string): Promise<void> {
  await apiClient.delete(`/financial/entries/${id}`);
}

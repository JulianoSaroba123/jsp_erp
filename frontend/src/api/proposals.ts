import { apiClient } from './client';

// ==================== TYPES ====================

export interface ProposalItem {
  id?: string;
  description: string;
  service_type: 'hora' | 'dia' | 'fechado';
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface ProposalProduct {
  id?: string;
  product_id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Proposal {
  id: string;
  number: string;
  customer_id: string;
  customer_name?: string;
  customer_contact?: string;
  title: string;
  description?: string;
  observations?: string;
  service_amount: number;
  parts_amount: number;
  discount_amount: number;
  total_amount: number;
  issue_date: string;
  validity_date?: string;
  approval_date?: string;
  status: 'rascunho' | 'enviada' | 'aprovada' | 'rejeitada' | 'cancelada';
  payment_condition?: string;
  delivery_days?: string;
  warranty_days?: string;
  user_id?: string;
  approved_by?: string;
  created_at: string;
  updated_at?: string;
  // Relações
  items?: ProposalItem[];
  products?: ProposalProduct[];
  // Controle de conversão
  has_service_order?: boolean;
}

export interface ProposalSummary {
  id: string;
  number: string;
  customer_name: string;
  title: string;
  total_amount: number;
  status: string;
  issue_date: string;
  has_service_order?: boolean;
}

export interface ProposalsResponse {
  items: ProposalSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateProposalData {
  customer_id: string;
  customer_contact?: string;
  title: string;
  description?: string;
  observations?: string;
  service_amount?: number;
  parts_amount?: number;
  discount_amount?: number;
  issue_date?: string;
  validity_date?: string;
  status?: 'rascunho' | 'enviada';
  payment_condition?: string;
  delivery_days?: string;
  warranty_days?: string;
  items?: ProposalItem[];
  products?: ProposalProduct[];
}

export interface UpdateProposalData {
  customer_contact?: string;
  title?: string;
  description?: string;
  observations?: string;
  service_amount?: number;
  parts_amount?: number;
  discount_amount?: number;
  validity_date?: string;
  payment_condition?: string;
  delivery_days?: string;
  warranty_days?: string;
}

export interface ConvertToOSRequest {
  technician_id?: string;
  expected_completion_date?: string;
  observations?: string;
}

export interface ConvertToOSResponse {
  success: boolean;
  message: string;
  service_order_id: string;
  service_order_number: string;
  proposal_number: string;
}

// ==================== HELPER FUNCTIONS ====================

export function getProposalStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    rascunho: 'Rascunho',
    enviada: 'Enviada',
    aprovada: 'Aprovada',
    rejeitada: 'Rejeitada',
    cancelada: 'Cancelada',
  };
  return labels[status] || status;
}

export function getProposalStatusColor(status: string): string {
  const colors: Record<string, string> = {
    rascunho: 'bg-gray-100 text-gray-800 border-gray-300',
    enviada: 'bg-blue-100 text-blue-800 border-blue-300',
    aprovada: 'bg-green-100 text-green-800 border-green-300',
    rejeitada: 'bg-red-100 text-red-800 border-red-300',
    cancelada: 'bg-gray-100 text-gray-600 border-gray-300',
  };
  return colors[status] || 'bg-gray-100 text-gray-800 border-gray-300';
}

export function getProposalStatusIcon(status: string): string {
  const icons: Record<string, string> = {
    rascunho: '📝',
    enviada: '📤',
    aprovada: '✅',
    rejeitada: '❌',
    cancelada: '🚫',
  };
  return icons[status] || '📄';
}

export function canConvertToOS(proposal: Proposal): boolean {
  return proposal.status === 'aprovada' && !proposal.has_service_order;
}

export function canEditProposal(proposal: Proposal): boolean {
  return ['rascunho', 'enviada'].includes(proposal.status);
}

export function canDeleteProposal(proposal: Proposal): boolean {
  // Não pode deletar aprovada com OS gerada
  if (proposal.status === 'aprovada' && proposal.has_service_order) {
    return false;
  }
  return true;
}

// ==================== API CALLS ====================

export async function getProposals(params: {
  page?: number;
  page_size?: number;
  status?: string;
  customer_id?: string;
  search?: string;
}): Promise<ProposalsResponse> {
  const response = await apiClient.get<ProposalsResponse>('/proposals', { params });
  return response.data;
}

export async function getProposalById(id: string): Promise<Proposal> {
  const response = await apiClient.get<Proposal>(`/proposals/${id}`);
  return response.data;
}

export async function getProposalByNumber(number: string): Promise<Proposal> {
  const response = await apiClient.get<Proposal>(`/proposals/number/${number}`);
  return response.data;
}

export async function createProposal(data: CreateProposalData): Promise<Proposal> {
  const response = await apiClient.post<Proposal>('/proposals', data);
  return response.data;
}

export async function updateProposal(id: string, data: UpdateProposalData): Promise<Proposal> {
  const response = await apiClient.patch<Proposal>(`/proposals/${id}`, data);
  return response.data;
}

export async function deleteProposal(id: string): Promise<void> {
  await apiClient.delete(`/proposals/${id}`);
}

export async function changeProposalStatus(
  id: string,
  newStatus: string
): Promise<Proposal> {
  const response = await apiClient.patch<Proposal>(
    `/proposals/${id}/status`,
    null,
    { params: { new_status: newStatus } }
  );
  return response.data;
}

/**
 * 🔥 CONVERSÃO: PROPOSTA APROVADA → ORDEM DE SERVIÇO
 * 
 * Esta é a função CENTRAL do fluxo de negócio.
 * 
 * Regras:
 * - Apenas propostas 'aprovada' podem converter (400 se não)
 * - Uma proposta só pode gerar UMA OS (409 se já existe)
 * - A OS gerada tem tipo_ordem='projeto' e exibir_valores=False
 */
export async function convertProposalToOS(
  id: string,
  data: ConvertToOSRequest
): Promise<ConvertToOSResponse> {
  const response = await apiClient.post<ConvertToOSResponse>(
    `/proposals/${id}/convert-to-os`,
    data
  );
  return response.data;
}

// ==================== ITEMS & PRODUCTS ====================

export async function getProposalItems(proposalId: string): Promise<ProposalItem[]> {
  const response = await apiClient.get<ProposalItem[]>(`/proposals/${proposalId}/items`);
  return response.data;
}

export async function addProposalItem(
  proposalId: string,
  data: ProposalItem
): Promise<ProposalItem> {
  const response = await apiClient.post<ProposalItem>(
    `/proposals/${proposalId}/items`,
    data
  );
  return response.data;
}

export async function getProposalProducts(proposalId: string): Promise<ProposalProduct[]> {
  const response = await apiClient.get<ProposalProduct[]>(`/proposals/${proposalId}/products`);
  return response.data;
}

export async function addProposalProduct(
  proposalId: string,
  data: ProposalProduct
): Promise<ProposalProduct> {
  const response = await apiClient.post<ProposalProduct>(
    `/proposals/${proposalId}/products`,
    data
  );
  return response.data;
}

// ==================== CÁLCULOS ====================

export function calculateProposalTotal(
  serviceAmount: number,
  partsAmount: number,
  discountAmount: number
): number {
  return serviceAmount + partsAmount - discountAmount;
}

export function calculateItemTotal(quantity: number, unitPrice: number): number {
  return quantity * unitPrice;
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
}

export function formatDate(dateString: string): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR');
}

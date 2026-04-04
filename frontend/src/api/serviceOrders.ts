import { apiClient } from './client';

// ==================== TYPES ====================

export interface ServiceOrderItem {
  id?: string;
  description: string;
  service_type: 'hora' | 'dia' | 'fechado';
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface ServiceOrderProduct {
  id?: string;
  product_id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface ServiceOrderInstallment {
  id?: string;
  installment_number: number;
  due_date: string;
  amount: number;
  paid: boolean;
  payment_date?: string;
}

export interface ServiceOrderAttachment {
  id: string;
  original_filename: string;
  stored_filename: string;
  file_type: 'image' | 'document' | 'pdf';
  mime_type?: string;
  file_size?: number;
  created_at: string;
}

export interface ServiceOrder {
  id: string;
  number: string;
  customer_id: string;
  customer_name?: string;
  // Tipo de Ordem de Serviço
  tipo_ordem: 'atendimento' | 'projeto';
  exibir_valores: boolean;
  proposta_id?: string;
  percentual_concluido: number;
  etapa_atual?: string;
  // Dados básicos
  title: string;
  description?: string;
  requester?: string;
  problem_description?: string;
  status: 'pendente' | 'em_execucao' | 'finalizada' | 'cancelada';
  priority: 'baixa' | 'normal' | 'alta' | 'urgente';
  opening_date: string;
  expected_date?: string;
  start_date?: string;
  completion_date?: string;
  technician?: string;
  equipment?: string;
  brand_model?: string;
  serial_number?: string;
  reported_defect?: string;
  technical_diagnosis?: string;
  solution?: string;
  notes?: string;
  start_time?: string;
  end_time?: string;
  total_hours?: string;
  initial_km?: number;
  final_km?: number;
  total_km?: string;
  service_amount: number;
  parts_amount: number;
  discount_amount: number;
  total_amount: number;
  warranty_days?: number;
  payment_condition: 'a_vista' | 'parcelado';
  installment_count?: number;
  down_payment?: number;
  first_installment_date?: string;
  payment_due_date?: string;
  payment_description?: string;
  payment_status: 'pendente' | 'parcial' | 'pago' | 'vencido';
  include_images_in_report: boolean;
  created_at: string;
  updated_at?: string;
  deleted_at?: string;
  items?: ServiceOrderItem[];
  products?: ServiceOrderProduct[];
  installments?: ServiceOrderInstallment[];
  attachments?: ServiceOrderAttachment[];
}

export interface ServiceOrdersResponse {
  items: ServiceOrder[];
  page: number;
  page_size: number;
  total: number;
}

export interface GetServiceOrdersParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  priority?: string;
  customer_id?: string;
  opening_date_start?: string;
  opening_date_end?: string;
}

export interface CreateServiceOrderData {
  customer_id: string;
  title: string;
  description?: string;
  requester?: string;
  problem_description?: string;
  priority?: 'baixa' | 'normal' | 'alta' | 'urgente';
  expected_date?: string;
  technician?: string;
  equipment?: string;
  brand_model?: string;
  serial_number?: string;
  reported_defect?: string;
  technical_diagnosis?: string;
  solution?: string;
  notes?: string;
  start_time?: string;
  end_time?: string;
  total_hours?: string;
  initial_km?: number;
  final_km?: number;
  total_km?: string;
  warranty_days?: number;
  payment_condition?: 'a_vista' | 'parcelado';
  installment_count?: number;
  down_payment?: number;
  first_installment_date?: string;
  payment_due_date?: string;
  payment_description?: string;
  include_images_in_report?: boolean;
  items?: Omit<ServiceOrderItem, 'id'>[];
  products?: Omit<ServiceOrderProduct, 'id'>[];
  installments?: Omit<ServiceOrderInstallment, 'id'>[];
}

export interface UpdateServiceOrderData {
  title?: string;
  description?: string;
  requester?: string;
  problem_description?: string;
  priority?: 'baixa' | 'normal' | 'alta' | 'urgente';
  expected_date?: string;
  technician?: string;
  equipment?: string;
  brand_model?: string;
  serial_number?: string;
  reported_defect?: string;
  technical_diagnosis?: string;
  solution?: string;
  notes?: string;
  start_time?: string;
  end_time?: string;
  total_hours?: string;
  initial_km?: number;
  final_km?: number;
  total_km?: string;
  warranty_days?: number;
  payment_condition?: 'a_vista' | 'parcelado';
  installment_count?: number;
  down_payment?: number;
  first_installment_date?: string;
  payment_due_date?: string;
  payment_description?: string;
  include_images_in_report?: boolean;
}

export interface ChangeStatusData {
  new_status: 'pendente' | 'em_execucao' | 'finalizada' | 'cancelada';
}

export interface DashboardStatistics {
  total: number;
  pendente: number;
  em_execucao: number;
  finalizada: number;
  cancelada: number;
  alta_prioridade: number;
  vencidas: number;
}

// ==================== API CALLS ====================

export const getServiceOrders = async (params?: GetServiceOrdersParams): Promise<ServiceOrdersResponse> => {
  const response = await apiClient.get<ServiceOrdersResponse>('/service-orders', { params });
  return response.data;
};

export const getServiceOrderById = async (id: string): Promise<ServiceOrder> => {
  const response = await apiClient.get<ServiceOrder>(`/service-orders/${id}`);
  return response.data;
};

export const getServiceOrderByNumber = async (number: string): Promise<ServiceOrder> => {
  const response = await apiClient.get<ServiceOrder>(`/service-orders/number/${number}`);
  return response.data;
};

export const createServiceOrder = async (data: CreateServiceOrderData): Promise<ServiceOrder> => {
  const response = await apiClient.post<ServiceOrder>('/service-orders', data);
  return response.data;
};

export const updateServiceOrder = async (id: string, data: UpdateServiceOrderData): Promise<ServiceOrder> => {
  const response = await apiClient.patch<ServiceOrder>(`/service-orders/${id}`, data);
  return response.data;
};

export const deleteServiceOrder = async (id: string): Promise<void> => {
  await apiClient.delete(`/service-orders/${id}`);
};

export const changeServiceOrderStatus = async (id: string, data: ChangeStatusData): Promise<ServiceOrder> => {
  const response = await apiClient.patch<ServiceOrder>(`/service-orders/${id}/status`, data);
  return response.data;
};

export const getDashboardStatistics = async (): Promise<DashboardStatistics> => {
  const response = await apiClient.get<DashboardStatistics>('/service-orders/statistics/dashboard');
  return response.data;
};

// ==================== ITEMS ====================

export const addServiceOrderItem = async (serviceOrderId: string, item: Omit<ServiceOrderItem, 'id'>): Promise<ServiceOrderItem> => {
  const response = await apiClient.post<ServiceOrderItem>(`/service-orders/${serviceOrderId}/items`, item);
  return response.data;
};

export const getServiceOrderItems = async (serviceOrderId: string): Promise<ServiceOrderItem[]> => {
  const response = await apiClient.get<ServiceOrderItem[]>(`/service-orders/${serviceOrderId}/items`);
  return response.data;
};

// ==================== PRODUCTS ====================

export const addServiceOrderProduct = async (serviceOrderId: string, product: Omit<ServiceOrderProduct, 'id'>): Promise<ServiceOrderProduct> => {
  const response = await apiClient.post<ServiceOrderProduct>(`/service-orders/${serviceOrderId}/products`, product);
  return response.data;
};

export const getServiceOrderProducts = async (serviceOrderId: string): Promise<ServiceOrderProduct[]> => {
  const response = await apiClient.get<ServiceOrderProduct[]>(`/service-orders/${serviceOrderId}/products`);
  return response.data;
};

// ==================== INSTALLMENTS ====================

export const addServiceOrderInstallment = async (serviceOrderId: string, installment: Omit<ServiceOrderInstallment, 'id'>): Promise<ServiceOrderInstallment> => {
  const response = await apiClient.post<ServiceOrderInstallment>(`/service-orders/${serviceOrderId}/installments`, installment);
  return response.data;
};

export const getServiceOrderInstallments = async (serviceOrderId: string): Promise<ServiceOrderInstallment[]> => {
  const response = await apiClient.get<ServiceOrderInstallment[]>(`/service-orders/${serviceOrderId}/installments`);
  return response.data;
};

// ==================== HELPER FUNCTIONS ====================

export const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pendente: 'Pendente',
    em_execucao: 'Em Execução',
    finalizada: 'Finalizada',
    cancelada: 'Cancelada',
  };
  return labels[status] || status;
};

export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pendente: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    em_execucao: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    finalizada: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    cancelada: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  };
  return colors[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
};

export const getPriorityLabel = (priority: string): string => {
  const labels: Record<string, string> = {
    baixa: 'Baixa',
    normal: 'Normal',
    alta: 'Alta',
    urgente: 'Urgente',
  };
  return labels[priority] || priority;
};

export const getPriorityColor = (priority: string): string => {
  const colors: Record<string, string> = {
    baixa: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    alta: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
    urgente: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  };
  return colors[priority] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
};

export const getTipoOrdemLabel = (tipo: string): string => {
  const labels: Record<string, string> = {
    atendimento: 'Atendimento',
    projeto: 'Projeto',
  };
  return labels[tipo] || tipo;
};

export const getTipoOrdemColor = (tipo: string): string => {
  const colors: Record<string, string> = {
    atendimento: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
    projeto: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-300',
  };
  return colors[tipo] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
};

export const getTipoOrdemIcon = (tipo: string): string => {
  const icons: Record<string, string> = {
    atendimento: '🚨',  // Emergencial/Chamado
    projeto: '📋',      // Projeto/Acompanhamento
  };
  return icons[tipo] || '📄';
};

export const getPaymentStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pendente: 'Pendente',
    parcial: 'Parcial',
    pago: 'Pago',
    vencido: 'Vencido',
  };
  return labels[status] || status;
};

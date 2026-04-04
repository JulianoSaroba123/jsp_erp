import { apiClient } from './client';

// TODO: Backend ainda não implementado - endpoints de exemplo baseados no padrão REST
// Quando backend estiver pronto, ajustar paths conforme /docs (pode ser /customers, /clients ou /clientes)

export interface Customer {
  id: string;
  person_type: 'PF' | 'PJ';
  name: string;
  trade_name?: string | null;
  cpf_cnpj?: string | null;
  state_registration?: string | null;
  email?: string | null;
  phone?: string | null;
  phone2?: string | null;
  // Endereço
  cep?: string | null;
  street?: string | null;
  number?: string | null;
  address_complement?: string | null;
  neighborhood?: string | null;
  city?: string | null;
  state?: string | null;
  // Adicionais
  notes?: string | null;
  status: 'active' | 'inactive';
  // Metadados
  created_at: string;
  updated_at?: string;
  deleted_at?: string | null;
}

export interface CustomersResponse {
  items: Customer[];
  page: number;
  page_size: number;
  total: number;
}

export interface GetCustomersParams {
  page?: number;
  page_size?: number;
}

export interface CreateCustomerData {
  person_type?: 'PF' | 'PJ';
  name: string;
  trade_name?: string;
  cpf_cnpj?: string;
  state_registration?: string;
  email?: string;
  phone?: string;
  phone2?: string;
  cep?: string;
  street?: string;
  number?: string;
  address_complement?: string;
  neighborhood?: string;
  city?: string;
  state?: string;
  notes?: string;
  status?: 'active' | 'inactive';
}

export interface UpdateCustomerData {
  person_type?: 'PF' | 'PJ';
  name?: string;
  trade_name?: string;
  cpf_cnpj?: string;
  state_registration?: string;
  email?: string;
  phone?: string;
  phone2?: string;
  cep?: string;
  street?: string;
  number?: string;
  address_complement?: string;
  neighborhood?: string;
  city?: string;
  state?: string;
  notes?: string;
  status?: 'active' | 'inactive';
}

export const getCustomers = async (params?: GetCustomersParams): Promise<CustomersResponse> => {
  // TODO: Ajustar path quando backend estiver pronto (verificar em /docs se é /customers, /clients ou /clientes)
  const response = await apiClient.get<CustomersResponse>('/customers', { params });
  return response.data;
};

export const createCustomer = async (data: CreateCustomerData): Promise<Customer> => {
  // TODO: Ajustar path quando backend estiver pronto
  const response = await apiClient.post<Customer>('/customers', data);
  return response.data;
};

export const patchCustomer = async (id: string, data: UpdateCustomerData): Promise<Customer> => {
  // TODO: Ajustar path quando backend estiver pronto
  const response = await apiClient.patch<Customer>(`/customers/${id}`, data);
  return response.data;
};

export const deleteCustomer = async (id: string): Promise<void> => {
  // TODO: Ajustar path quando backend estiver pronto
  await apiClient.delete(`/customers/${id}`);
};

import { apiClient } from './client';

export interface Order {
  id: string;
  user_id: string;
  description: string;
  total: number;
  status: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface OrdersResponse {
  items: Order[];
  page: number;
  page_size: number;
  total: number;
}

export interface GetOrdersParams {
  page?: number;
  page_size?: number;
}

export interface CreateOrderData {
  description: string;
  total: number;
}

export interface UpdateOrderData {
  description?: string;
  total?: number;
}

export const getOrders = async (params?: GetOrdersParams): Promise<OrdersResponse> => {
  const response = await apiClient.get<OrdersResponse>('/orders', { params });
  return response.data;
};

export const createOrder = async (data: CreateOrderData): Promise<Order> => {
  const response = await apiClient.post<Order>('/orders', data);
  return response.data;
};

export const patchOrder = async (id: string, data: UpdateOrderData): Promise<Order> => {
  const response = await apiClient.patch<Order>(`/orders/${id}`, data);
  return response.data;
};

export const deleteOrder = async (id: string): Promise<void> => {
  await apiClient.delete(`/orders/${id}`);
};

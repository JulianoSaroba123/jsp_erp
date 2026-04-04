import { apiClient } from './client';

export interface Product {
  id: string;
  user_id: string;
  code?: string | null;
  name: string;
  category?: string | null;
  subcategoria?: string | null;
  unit?: string | null;
  description?: string | null;
  
  // Identificação Estendida
  codigo_barras?: string | null;
  marca?: string | null;
  modelo?: string | null;
  
  // Físico
  peso?: number | null;
  dimensoes?: string | null;
  
  // Preços
  cost_price: number;
  sale_price: number;
  markup?: number | null;
  margem_lucro?: number | null;
  
  // Estoque
  stock_qty: number;
  stock_min: number;
  estoque_maximo?: number | null;
  controla_estoque: boolean;
  
  // Relacionamentos e Observações
  fornecedor_id?: string | null;
  observacoes?: string | null;
  
  active: boolean;
  created_at: string;
  updated_at?: string;
  deleted_at?: string | null;
  
  // Computed (do backend)
  valor_estoque?: number;
  situacao_estoque?: string;
  margem_lucro_calculada?: number;
}

export interface ProductsResponse {
  items: Product[];
  page: number;
  page_size: number;
  total: number;
}

export interface GetProductsParams {
  page?: number;
  page_size?: number;
  q?: string;
  category?: string;
  active?: boolean;
}

export interface CreateProductData {
  code?: string;
  name: string;
  category?: string;
  subcategoria?: string;
  unit?: string;
  description?: string;
  
  // Identificação Estendida
  codigo_barras?: string;
  marca?: string;
  modelo?: string;
  
  // Físico
  peso?: number;
  dimensoes?: string;
  
  // Preços
  cost_price?: number;
  sale_price?: number;
  markup?: number;
  margem_lucro?: number;
  
  // Estoque
  stock_qty?: number;
  stock_min?: number;
  estoque_maximo?: number;
  controla_estoque?: boolean;
  
  // Relacionamentos e Observações
  fornecedor_id?: string;
  observacoes?: string;
  
  active?: boolean;
}

export interface UpdateProductData {
  code?: string;
  name?: string;
  category?: string;
  subcategoria?: string;
  unit?: string;
  description?: string;
  
  // Identificação Estendida
  codigo_barras?: string;
  marca?: string;
  modelo?: string;
  
  // Físico
  peso?: number;
  dimensoes?: string;
  
  // Preços
  cost_price?: number;
  sale_price?: number;
  markup?: number;
  margem_lucro?: number;
  
  // Estoque
  stock_qty?: number;
  stock_min?: number;
  estoque_maximo?: number;
  controla_estoque?: boolean;
  
  // Relacionamentos e Observações
  fornecedor_id?: string;
  observacoes?: string;
  
  active?: boolean;
}

export const getProducts = async (params?: GetProductsParams): Promise<ProductsResponse> => {
  const response = await apiClient.get<ProductsResponse>('/products', { params });
  return response.data;
};

export const getProduct = async (id: string): Promise<Product> => {
  const response = await apiClient.get<Product>(`/products/${id}`);
  return response.data;
};

export const createProduct = async (data: CreateProductData): Promise<Product> => {
  const response = await apiClient.post<Product>('/products', data);
  return response.data;
};

export const updateProduct = async (id: string, data: UpdateProductData): Promise<Product> => {
  const response = await apiClient.patch<Product>(`/products/${id}`, data);
  return response.data;
};

export const deleteProduct = async (id: string): Promise<void> => {
  await apiClient.delete(`/products/${id}`);
};

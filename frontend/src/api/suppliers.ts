/**
 * API Client para Suppliers (Fornecedores)
 * Tipagem completa com interfaces TypeScript
 */

import { apiClient } from './client';

// ==================== INTERFACES ====================

export interface Supplier {
  // Identificação
  id: string;
  user_id: string;
  
  // Dados Principais
  nome: string;
  nome_fantasia?: string;
  tipo: 'PF' | 'PJ';
  
  // Documentos
  cnpj_cpf: string;
  rg_ie?: string;
  inscricao_estadual?: string;
  inscricao_municipal?: string;
  im?: string;
  
  // Contato
  email?: string;
  email_financeiro?: string;
  telefone?: string;
  celular?: string;
  whatsapp?: string;
  site?: string;
  website?: string;
  
  // Contato Comercial
  contato_nome?: string;
  contato_cargo?: string;
  contato_email?: string;
  contato_telefone?: string;
  
  // Endereço
  cep?: string;
  endereco?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  estado?: string;
  pais?: string;
  
  // Segmentação
  segmento?: string;
  porte_empresa?: string;
  origem?: string;
  classificacao?: string;
  categoria?: string;
  categoria_fiscal?: string;
  
  // Comercial
  condicoes_pagamento?: string;
  prazo_entrega?: string;
  forma_entrega?: string;
  tempo_entrega_medio?: string;
  
  // Financeiro
  limite_credito?: number;
  prazo_pagamento_padrao?: number;
  desconto_padrao?: number;
  
  // Datas
  data_nascimento?: string;
  data_fundacao?: string;
  
  // Pessoais (PF)
  genero?: string;
  estado_civil?: string;
  profissao?: string;
  
  // Específicos
  certificacoes?: string;
  
  // Bancário
  banco_principal?: string;
  agencia?: string;
  conta?: string;
  pix?: string;
  
  // Gestão
  observacoes?: string;
  observacoes_internas?: string;
  status?: string;
  motivo_bloqueio?: string;
  ativo: boolean;
  
  // Auditoria
  created_at: string;
  updated_at: string;
  
  // Computed (do backend)
  documento_formatado: string;
  nome_display: string;
  endereco_completo: string;
  contato_principal: string;
  is_pessoa_juridica: boolean;
  is_pessoa_fisica: boolean;
  telefone_formatado: string;
  celular_formatado: string;
}

export interface CreateSupplierData {
  // Campos obrigatórios
  nome: string;
  tipo: 'PF' | 'PJ';
  cnpj_cpf: string;
  
  // Todos os outros campos opcionais
  nome_fantasia?: string;
  rg_ie?: string;
  inscricao_estadual?: string;
  inscricao_municipal?: string;
  im?: string;
  email?: string;
  email_financeiro?: string;
  telefone?: string;
  celular?: string;
  whatsapp?: string;
  site?: string;
  website?: string;
  contato_nome?: string;
  contato_cargo?: string;
  contato_email?: string;
  contato_telefone?: string;
  cep?: string;
  endereco?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  estado?: string;
  pais?: string;
  segmento?: string;
  porte_empresa?: string;
  origem?: string;
  classificacao?: string;
  categoria?: string;
  categoria_fiscal?: string;
  condicoes_pagamento?: string;
  prazo_entrega?: string;
  forma_entrega?: string;
  tempo_entrega_medio?: string;
  limite_credito?: number;
  prazo_pagamento_padrao?: number;
  desconto_padrao?: number;
  data_nascimento?: string;
  data_fundacao?: string;
  genero?: string;
  estado_civil?: string;
  profissao?: string;
  certificacoes?: string;
  banco_principal?: string;
  agencia?: string;
  conta?: string;
  pix?: string;
  observacoes?: string;
  observacoes_internas?: string;
  status?: string;
  motivo_bloqueio?: string;
  ativo?: boolean;
}

export interface UpdateSupplierData extends Partial<CreateSupplierData> {}

export interface SupplierFilters {
  search?: string;
  tipo?: 'PF' | 'PJ';
  categoria?: string;
  classificacao?: string;
  cidade?: string;
  estado?: string;
  ativo?: boolean;
  skip?: number;
  limit?: number;
}

export interface CNPJData {
  nome: string;
  nome_fantasia: string;
  cnpj: string;
  email: string;
  telefone: string;
  situacao: string;
  data_abertura?: string;
  porte?: string;
  natureza_juridica?: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  municipio: string;
  uf: string;
}

export interface CEPData {
  cep: string;
  logradouro: string;
  complemento: string;
  bairro: string;
  localidade: string;
  cidade: string;
  uf: string;
  ibge?: string;
  gia?: string;
  ddd?: string;
  siafi?: string;
}

export interface AutocompleteResult {
  id: string;
  nome_display: string;
  documento_formatado: string;
  tipo: 'PF' | 'PJ';
  categoria?: string;
}

export interface SupplierStats {
  total: number;
  por_tipo: {
    PF: number;
    PJ: number;
  };
  por_categoria: Array<{
    categoria: string;
    count: number;
  }>;
}

// ==================== API FUNCTIONS ====================

export const suppliersAPI = {
  /**
   * Lista suppliers com filtros
   */
  list: async (filters?: SupplierFilters): Promise<Supplier[]> => {
    const params = new URLSearchParams();
    
    // Adicionar parâmetros de paginação padrão
    params.append('page', '1');
    params.append('page_size', '100');
    
    if (filters) {
      if (filters.search) params.append('search', filters.search);
      if (filters.tipo) params.append('tipo', filters.tipo);
      if (filters.categoria) params.append('categoria', filters.categoria);
      if (filters.classificacao) params.append('classificacao', filters.classificacao);
      if (filters.cidade) params.append('cidade', filters.cidade);
      if (filters.estado) params.append('estado', filters.estado);
      if (filters.ativo !== undefined) params.append('ativo', filters.ativo.toString());
      if (filters.skip) params.append('skip', filters.skip.toString());
      if (filters.limit) params.append('limit', filters.limit.toString());
    }
    
    const response = await apiClient.get(`/suppliers?${params.toString()}`);
    // Backend agora retorna {items, page, page_size, total}
    return response.data.items || [];
  },

  /**
   * Busca supplier por ID
   */
  getById: async (id: string): Promise<Supplier> => {
    const response = await apiClient.get(`/suppliers/${id}`);
    return response.data;
  },

  /**
   * Cria novo supplier
   */
  create: async (data: CreateSupplierData): Promise<Supplier> => {
    const response = await apiClient.post('/suppliers', data);
    return response.data;
  },

  /**
   * Atualiza supplier
   */
  update: async (id: string, data: UpdateSupplierData): Promise<Supplier> => {
    const response = await apiClient.patch(`/suppliers/${id}`, data);
    return response.data;
  },

  /**
   * Delete supplier (soft delete)
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/suppliers/${id}`);
  },

  /**
   * Autocomplete para busca rápida
   */
  autocomplete: async (query: string, limit: number = 10): Promise<AutocompleteResult[]> => {
    const response = await apiClient.get('/suppliers/search/autocomplete', {
      params: { q: query, limit }
    });
    return response.data;
  },

  /**
   * Consulta CNPJ na ReceitaWS (auto-fill)
   */
  consultarCNPJ: async (cnpj: string): Promise<CNPJData> => {
    const response = await apiClient.get(`/suppliers/api/cnpj/${cnpj}`);
    if (response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data.error || 'Erro ao consultar CNPJ');
  },

  /**
   * Consulta CEP no ViaCEP (auto-fill endereço)
   */
  consultarCEP: async (cep: string): Promise<CEPData> => {
    const response = await apiClient.get(`/suppliers/api/cep/${cep}`);
    if (response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data.error || 'Erro ao consultar CEP');
  },

  /**
   * Estatísticas de suppliers
   */
  getStats: async (): Promise<SupplierStats> => {
    const response = await apiClient.get('/suppliers/stats/summary');
    return response.data;
  }
};

export default suppliersAPI;

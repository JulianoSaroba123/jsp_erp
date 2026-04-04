/**
 * APIs externas (BrasilAPI, ViaCEP)
 * Não usam o apiClient do ERP (chamadas diretas)
 */

import axios from 'axios';

// Tipos BrasilAPI (campos completos da API v1)
export interface BrasilAPICnpjResponse {
  cnpj: string;
  razao_social: string;
  nome_fantasia: string;
  descricao_situacao_cadastral: string;
  situacao_cadastral: string;
  data_inicio_atividade: string; // "YYYY-MM-DD"
  data_situacao_cadastral: string;
  
  // Endereço
  cep: string;
  logradouro: string;
  numero: string;
  complemento?: string;
  bairro: string;
  municipio: string;
  uf: string;
  
  // Contato
  email?: string;
  ddd_telefone_1?: string;
  ddd_telefone_2?: string;
  ddd_fax?: string;
  
  // Empresa
  capital_social?: string; // valor numérico em string
  porte: string; // "DEMAIS", "ME", "EPP", etc
  natureza_juridica: string;
  
  // CNAE
  cnae_fiscal: number;
  cnae_fiscal_descricao: string;
  
  // QSA (Quadro Societário)
  qsa?: Array<{
    nome_socio: string;
    cnpj_cpf_do_socio: string;
    qualificacao_socio: string;
    codigo_qualificacao_socio: number;
    percentual_capital_social: number;
    data_entrada_sociedade: string;
    cpf_representante_legal?: string;
    nome_representante_legal?: string;
    codigo_qualificacao_representante_legal?: number;
  }>;
}

// Tipos ViaCEP
export interface ViaCepResponse {
  cep: string;
  logradouro: string;
  complemento: string;
  bairro: string;
  localidade: string;
  uf: string;
  erro?: boolean; // ViaCEP retorna { erro: true } quando não encontra
}

/**
 * Busca dados de empresa por CNPJ na BrasilAPI
 * @param cnpj - CNPJ com 14 dígitos (somente números)
 * @throws Error se CNPJ inválido ou não encontrado
 */
export async function getCompanyByCnpj(cnpj: string): Promise<BrasilAPICnpjResponse> {
  // Remove caracteres não numéricos
  const cleanCnpj = cnpj.replace(/\D/g, '');
  
  if (cleanCnpj.length !== 14) {
    throw new Error('CNPJ deve ter 14 dígitos');
  }

  try {
    const response = await axios.get<BrasilAPICnpjResponse>(
      `https://brasilapi.com.br/api/cnpj/v1/${cleanCnpj}`,
      { timeout: 10000 }
    );
    
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error('CNPJ não encontrado');
    }
    if (error.code === 'ECONNABORTED') {
      throw new Error('Timeout ao consultar BrasilAPI');
    }
    throw new Error('Erro ao consultar CNPJ na BrasilAPI');
  }
}

/**
 * Busca endereço por CEP na ViaCEP
 * @param cep - CEP com 8 dígitos (somente números)
 * @throws Error se CEP inválido ou não encontrado
 */
export async function getAddressByCep(cep: string): Promise<ViaCepResponse> {
  // Remove caracteres não numéricos
  const cleanCep = cep.replace(/\D/g, '');
  
  if (cleanCep.length !== 8) {
    throw new Error('CEP deve ter 8 dígitos');
  }

  try {
    const response = await axios.get<ViaCepResponse>(
      `https://viacep.com.br/ws/${cleanCep}/json/`,
      { timeout: 8000 }
    );
    
    // ViaCEP retorna { erro: true } quando CEP não existe
    if (response.data.erro) {
      throw new Error('CEP não encontrado');
    }
    
    return response.data;
  } catch (error: any) {
    if (error.message === 'CEP não encontrado') {
      throw error;
    }
    if (error.code === 'ECONNABORTED') {
      throw new Error('Timeout ao consultar ViaCEP');
    }
    throw new Error('Erro ao consultar CEP no ViaCEP');
  }
}

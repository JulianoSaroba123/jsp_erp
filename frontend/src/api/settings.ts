import { apiClient } from './client';

// ============================================================================
// TYPES
// ============================================================================

export interface Settings {
  // Empresa
  company_name: string;
  trade_name?: string;
  cnpj?: string;
  email?: string;
  phone?: string;
  cep?: string;
  street?: string;
  number?: string;
  neighborhood?: string;
  city?: string;
  state?: string;
  logo_url?: string;
  
  // Sistema
  theme: 'light' | 'dark';
  timezone: string;
  currency: string;
  
  // Documentos
  pdf_header_text?: string;
  pdf_footer_text?: string;
  default_proposal_message?: string;
}

export interface SettingsUpdate extends Partial<Settings> {}

export interface UploadLogoResponse {
  logo_url: string;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STORAGE_KEY = 'erp_settings_v1';

const DEFAULT_SETTINGS: Settings = {
  company_name: '',
  theme: 'light',
  timezone: 'America/Sao_Paulo',
  currency: 'BRL',
};

// ============================================================================
// HELPER FUNCTIONS (localStorage fallback)
// ============================================================================

function getSettingsFromStorage(): Settings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch (error) {
    console.error('Erro ao ler settings do localStorage:', error);
  }
  return DEFAULT_SETTINGS;
}

function saveSettingsToStorage(settings: Settings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch (error) {
    console.error('Erro ao salvar settings no localStorage:', error);
    throw new Error('Erro ao salvar configurações localmente');
  }
}

// ============================================================================
// API FUNCTIONS (com fallback para localStorage)
// ============================================================================

/**
 * Busca as configurações do sistema.
 * Tenta backend primeiro, se falhar usa localStorage.
 */
export const getSettings = async (): Promise<Settings> => {
  try {
    const response = await apiClient.get<Settings>('/settings');
    return response.data;
  } catch (error: any) {
    // Se backend não existir (404/501) ou falhar, usar localStorage
    if (error.response?.status === 404 || error.response?.status === 501 || !error.response) {
      console.warn('Backend /settings não disponível, usando localStorage');
      return getSettingsFromStorage();
    }
    throw error;
  }
};

/**
 * Atualiza as configurações do sistema.
 * Tenta backend primeiro, se falhar usa localStorage.
 */
export const updateSettings = async (data: SettingsUpdate): Promise<Settings> => {
  try {
    const response = await apiClient.put<Settings>('/settings', data);
    return response.data;
  } catch (error: any) {
    // Se backend não existir (404/501) ou falhar, usar localStorage
    if (error.response?.status === 404 || error.response?.status === 501 || !error.response) {
      console.warn('Backend PUT /settings não disponível, salvando no localStorage');
      const currentSettings = getSettingsFromStorage();
      const updatedSettings = { ...currentSettings, ...data };
      saveSettingsToStorage(updatedSettings);
      return updatedSettings;
    }
    throw error;
  }
};

/**
 * Faz upload do logo da empresa.
 * Se backend não estiver disponível, salva como base64 no localStorage.
 */
export const uploadLogo = async (file: File): Promise<UploadLogoResponse> => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post<UploadLogoResponse>('/settings/logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error: any) {
    // Se backend não existir, converter para base64 e salvar
    if (error.response?.status === 404 || error.response?.status === 501 || !error.response) {
      console.warn('Backend POST /settings/logo não disponível, salvando como base64');
      
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result as string;
          resolve({ logo_url: base64 });
        };
        reader.onerror = () => reject(new Error('Erro ao ler arquivo'));
        reader.readAsDataURL(file);
      });
    }
    throw error;
  }
};

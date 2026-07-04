import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings, uploadLogo, Settings } from '../api/settings';
import { CompanySettingsForm } from './Settings/CompanySettingsForm';
import { SystemSettingsForm } from './Settings/SystemSettingsForm';
import { DocumentsSettingsForm } from './Settings/DocumentsSettingsForm';
import { LoadingState, ErrorState } from '../components/ui/State';
import { usePermissions } from '../auth/usePermissions';

type Tab = 'empresa' | 'sistema' | 'documentos';

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { hasPermission } = usePermissions();
  const [activeTab, setActiveTab] = useState<Tab>('empresa');

  const canRead = hasPermission('settings:read');
  const canUpdate = hasPermission('settings:update');

  // Query para buscar settings
  const { data: settings, isLoading, error } = useQuery<Settings>({
    queryKey: ['settings'],
    queryFn: getSettings,
    enabled: canRead,
  });

  // Mutation para atualizar settings
  const mutation = useMutation({
    mutationFn: async (data: Partial<Settings>) => {
      console.log('🟢 [Settings] Mutation iniciada com:', data);
      
      // Se houver upload de logo, fazer upload primeiro
      if ((data as any)._logoFile) {
        const logoFile = (data as any)._logoFile;
        delete (data as any)._logoFile;
        
        try {
          console.log('📤 [Settings] Fazendo upload do logo...');
          const { logo_url } = await uploadLogo(logoFile);
          data.logo_url = logo_url;
          console.log('✅ [Settings] Logo enviado:', logo_url);
        } catch (error) {
          console.error('❌ [Settings] Erro ao fazer upload do logo:', error);
          // Continuar mesmo se upload falhar
        }
      }
      
      console.log('💾 [Settings] Chamando updateSettings...');
      const result = await updateSettings(data);
      console.log('✅ [Settings] Settings atualizadas:', result);
      return result;
    },
    onSuccess: (data) => {
      console.log('🎉 [Settings] Mutation sucesso!', data);
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: (error) => {
      console.error('❌ [Settings] Mutation erro:', error);
    },
  });

  // Se não tiver permissão de leitura
  if (!canRead) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <svg className="w-6 h-6 text-red-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <h3 className="text-lg font-semibold text-red-900">Acesso Negado</h3>
                <p className="mt-1 text-sm text-red-700">
                  Você não tem permissão para visualizar as configurações do sistema.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <LoadingState title="Carregando configurações..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Erro ao carregar configurações"
        description={(error as any)?.message || 'Não foi possível carregar as configurações do sistema'}
        onRetry={() => queryClient.invalidateQueries({ queryKey: ['settings'] })}
      />
    );
  }

  if (!settings) {
    return <ErrorState title="Configurações não encontradas" />;
  }

  const handleSave = (data: Partial<Settings>) => {
    console.log('🟡 [Settings] handleSave chamado:', data);
    console.log('🟡 [Settings] canUpdate:', canUpdate);
    console.log('🟡 [Settings] mutation.isPending:', mutation.isPending);
    mutation.mutate(data);
  };

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'empresa', label: 'Empresa', icon: '🏢' },
    { id: 'sistema', label: 'Sistema', icon: '⚙️' },
    { id: 'documentos', label: 'Documentos', icon: '📄' },
  ];

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Configurações</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Gerencie as configurações gerais do sistema ERP
          </p>
        </div>

        {/* Mensagem de Sucesso */}
        {mutation.isSuccess && (
          <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-600 dark:text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-sm font-medium text-green-900 dark:text-green-300">
                Configurações salvas com sucesso!
              </p>
            </div>
          </div>
        )}

        {/* Erro ao Salvar */}
        {mutation.isError && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-600 dark:text-red-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-sm font-medium text-red-900 dark:text-red-300">
                Erro ao salvar: {(mutation.error as any)?.message || 'Erro desconhecido'}
              </p>
            </div>
          </div>
        )}

        {/* Alerta se não tiver permissão de edição */}
        {!canUpdate && (
          <div className="mb-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-amber-600 dark:text-amber-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-amber-900 dark:text-amber-300">
                Você tem permissão apenas para visualizar as configurações, mas não pode editá-las.
              </p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          {/* Tab Headers */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'empresa' && (
              <CompanySettingsForm
                settings={settings}
                onSave={handleSave}
                isSaving={mutation.isPending}
                canEdit={canUpdate}
              />
            )}

            {activeTab === 'sistema' && (
              <SystemSettingsForm
                settings={settings}
                onSave={handleSave}
                isSaving={mutation.isPending}
                canEdit={canUpdate}
              />
            )}

            {activeTab === 'documentos' && (
              <DocumentsSettingsForm
                settings={settings}
                onSave={handleSave}
                isSaving={mutation.isPending}
                canEdit={canUpdate}
              />
            )}
          </div>
        </div>

        {/* Informação sobre Persistência */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-blue-900">
                💾 Persistência de Dados
              </h4>
              <p className="mt-1 text-sm text-blue-700">
                {settings.logo_url?.startsWith('data:') 
                  ? 'Dados salvos localmente no navegador. Para persistência em servidor, configure o backend.'
                  : 'Configurações sincronizadas com o servidor.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

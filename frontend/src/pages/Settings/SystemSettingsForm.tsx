import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Settings } from '../../api/settings';
import { useTheme } from '../../contexts/ThemeContext';

const systemSchema = z.object({
  theme: z.enum(['light', 'dark']),
  timezone: z.string(),
  currency: z.string(),
});

type SystemFormData = z.infer<typeof systemSchema>;

interface SystemSettingsFormProps {
  settings: Settings;
  onSave: (data: Partial<Settings>) => void;
  isSaving: boolean;
  canEdit: boolean;
}

export function SystemSettingsForm({ settings, onSave, isSaving, canEdit }: SystemSettingsFormProps) {
  const { setTheme } = useTheme();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<SystemFormData>({
    resolver: zodResolver(systemSchema),
    defaultValues: {
      theme: settings.theme || 'light',
      timezone: settings.timezone || 'America/Sao_Paulo',
      currency: settings.currency || 'BRL',
    },
  });

  const handleRadioClick = (newTheme: 'light' | 'dark') => {
    setValue('theme', newTheme);
    setTheme(newTheme);
  };

  const onSubmit = (data: SystemFormData) => {
    onSave(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="bg-gray-50 dark:bg-gray-700/50 p-6 rounded-lg border border-gray-200 dark:border-gray-600 space-y-4">
        {/* Tema */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Tema da Interface
          </label>
          <div className="flex gap-4">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                value="light"
                {...register('theme')}
                onClick={() => handleRadioClick('light')}
                disabled={!canEdit}
                className="mr-2 disabled:cursor-not-allowed cursor-pointer"
              />
              ☀️ Claro
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                value="dark"
                {...register('theme')}
                onClick={() => handleRadioClick('dark')}
                disabled={!canEdit}
                className="mr-2 disabled:cursor-not-allowed cursor-pointer"
              />
              🌙 Escuro
            </label>
          </div>
          {errors.theme && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.theme.message}</p>}
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            O tema é aplicado instantaneamente ao selecionar uma opção.
          </p>
        </div>

        {/* Timezone */}
        <div>
          <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Fuso Horário
          </label>
          <select
            id="timezone"
            {...register('timezone')}
            disabled={!canEdit}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            <option value="America/Sao_Paulo">América/São Paulo (BRT - UTC-3)</option>
            <option value="America/Manaus">América/Manaus (AMT - UTC-4)</option>
            <option value="America/Fortaleza">América/Fortaleza (BRT - UTC-3)</option>
            <option value="America/Recife">América/Recife (BRT - UTC-3)</option>
            <option value="America/Noronha">Fernando de Noronha (FNT - UTC-2)</option>
          </select>
          {errors.timezone && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.timezone.message}</p>}
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Define o fuso horário usado em relatórios e timestamps do sistema.
          </p>
        </div>

        {/* Moeda */}
        <div>
          <label htmlFor="currency" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Moeda Padrão
          </label>
          <select
            id="currency"
            {...register('currency')}
            disabled={!canEdit}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            <option value="BRL">Real Brasileiro (R$)</option>
            <option value="USD">Dólar Americano (US$)</option>
            <option value="EUR">Euro (€)</option>
          </select>
          {errors.currency && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.currency.message}</p>}
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Define a moeda usada em relatórios financeiros e documentos.
          </p>
        </div>
      </div>

      {/* Informações Adicionais */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <h4 className="text-sm font-medium text-blue-900 dark:text-blue-300">
              Configurações do Sistema
            </h4>
            <p className="mt-1 text-sm text-blue-700 dark:text-blue-400">
              Estas configurações afetam toda a aplicação e são aplicadas globalmente para todos os usuários.
            </p>
          </div>
        </div>
      </div>

      {/* Botão Salvar */}
      {canEdit && (
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-600">
          <button
            type="submit"
            disabled={isSaving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:ring-offset-gray-800 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      )}
    </form>
  );
}

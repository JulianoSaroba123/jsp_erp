import { useAuth } from '../../auth/useAuth';
import { useTheme } from '../../contexts/ThemeContext';
import { useQuery } from '@tanstack/react-query';
import { getSettings } from '../../api/settings';

export function Header() {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  // Usar React Query para carregar configurações e reagir a mudanças
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
    staleTime: 1000 * 60 * 5, // Cache por 5 minutos
    retry: 1,
  });

  // Priorizar nome fantasia, se não houver usar razão social
  const companyName = settings?.trade_name || settings?.company_name || 'ERP System';
  const logoUrl = settings?.logo_url;

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700 px-6 py-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          {logoUrl && (
            <img 
              src={logoUrl} 
              alt={companyName}
              className="h-8 w-8 object-contain"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
          )}
          <h1 className="text-xl font-semibold text-gray-800 dark:text-gray-100">{companyName}</h1>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-200 dark:bg-gray-700 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            title={theme === 'dark' ? 'Modo claro' : 'Modo escuro'}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button
            onClick={logout}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:ring-offset-gray-800"
          >
            Sair
          </button>
        </div>
      </div>
    </header>
  );
}

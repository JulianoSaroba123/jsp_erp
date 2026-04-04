/**
 * Componentes padronizados de estado de UI
 * Loading, Error e Empty states com acessibilidade
 */

interface LoadingStateProps {
  title?: string;
  description?: string;
}

export function LoadingState({ 
  title = 'Carregando…', 
  description 
}: LoadingStateProps) {
  return (
    <div className="flex items-center justify-center min-h-64 py-12">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
        {description && (
          <p className="text-sm text-gray-600">{description}</p>
        )}
      </div>
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
}

export function ErrorState({ 
  title = 'Erro ao carregar', 
  description = 'Não foi possível carregar. Tente novamente.',
  onRetry 
}: ErrorStateProps) {
  return (
    <div className="flex items-center justify-center min-h-64 py-12">
      <div className="text-center max-w-md">
        <div className="bg-red-100 rounded-full h-16 w-16 flex items-center justify-center mx-auto mb-4">
          <span className="text-red-600 text-3xl">⚠️</span>
        </div>
        <h3 className="text-lg font-semibold text-red-800 mb-2">{title}</h3>
        <p className="text-sm text-red-600 mb-4">{description}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
          >
            🔄 Tentar novamente
          </button>
        )}
      </div>
    </div>
  );
}

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ 
  title = 'Nenhum registro encontrado', 
  description,
  actionLabel,
  onAction 
}: EmptyStateProps) {
  return (
    <div className="flex items-center justify-center min-h-64 py-12">
      <div className="text-center max-w-md">
        <div className="bg-gray-100 rounded-full h-16 w-16 flex items-center justify-center mx-auto mb-4">
          <span className="text-gray-400 text-3xl">📭</span>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
        {description && (
          <p className="text-sm text-gray-600 mb-4">{description}</p>
        )}
        {onAction && actionLabel && (
          <button
            onClick={onAction}
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  );
}

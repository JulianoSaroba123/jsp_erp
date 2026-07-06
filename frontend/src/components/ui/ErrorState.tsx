import type { ReactNode } from 'react';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  description?: string;
  icon?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}

export function ErrorState({
  title = 'Falha ao carregar',
  description = 'Tente novamente em instantes.',
  icon,
  actionLabel = 'Tentar novamente',
  onAction,
}: ErrorStateProps) {
  return (
    <div
      className="w-full py-12 px-4 text-center border"
      style={{
        borderColor: 'rgba(220,38,38,0.35)',
        backgroundColor: 'rgba(220,38,38,0.05)',
        borderRadius: 'var(--radius-lg)',
      }}
    >
      {icon && <div className="mb-3 flex justify-center" style={{ color: 'var(--color-danger-500)' }}>{icon}</div>}
      <h3 className="text-lg font-semibold" style={{ color: 'var(--color-danger-500)' }}>{title}</h3>
      <p className="mt-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>{description}</p>
      {onAction && (
        <div className="mt-4">
          <Button variant="danger" onClick={onAction}>{actionLabel}</Button>
        </div>
      )}
    </div>
  );
}

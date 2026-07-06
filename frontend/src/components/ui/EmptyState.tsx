import type { ReactNode } from 'react';
import { Button } from './Button';

export interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  title = 'Nenhum dado encontrado',
  description,
  icon,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="w-full py-12 px-4 text-center border" style={{ borderColor: 'var(--color-border)', borderRadius: 'var(--radius-lg)' }}>
      {icon && <div className="mb-3 flex justify-center" style={{ color: 'var(--color-text-muted)' }}>{icon}</div>}
      <h3 className="text-lg font-semibold" style={{ color: 'var(--color-text)' }}>{title}</h3>
      {description && (
        <p className="mt-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <div className="mt-4">
          <Button onClick={onAction}>{actionLabel}</Button>
        </div>
      )}
    </div>
  );
}

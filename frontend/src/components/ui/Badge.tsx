import type { HTMLAttributes } from 'react';

type BadgeVariant = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

function getBadgeStyle(variant: BadgeVariant): React.CSSProperties {
  switch (variant) {
    case 'success':
      return { backgroundColor: 'rgba(22,163,74,0.12)', color: 'var(--color-success-500)' };
    case 'warning':
      return { backgroundColor: 'rgba(245,158,11,0.12)', color: 'var(--color-warning-500)' };
    case 'danger':
      return { backgroundColor: 'rgba(220,38,38,0.12)', color: 'var(--color-danger-500)' };
    case 'info':
      return { backgroundColor: 'rgba(14,165,233,0.12)', color: 'var(--color-info-500)' };
    default:
      return { backgroundColor: 'var(--color-surface-muted)', color: 'var(--color-text-muted)' };
  }
}

export function Badge({ variant = 'neutral', className = '', children, ...props }: BadgeProps) {
  return (
    <span
      className={['inline-flex items-center px-2.5 py-1 text-xs font-semibold', className].join(' ')}
      style={{ borderRadius: 'var(--radius-full)', ...getBadgeStyle(variant) }}
      {...props}
    >
      {children}
    </span>
  );
}

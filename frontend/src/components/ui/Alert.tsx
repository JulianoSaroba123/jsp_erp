import type { HTMLAttributes, ReactNode } from 'react';

type AlertVariant = 'info' | 'success' | 'warning' | 'danger';

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  icon?: ReactNode;
}

function getAlertStyles(variant: AlertVariant): React.CSSProperties {
  switch (variant) {
    case 'success':
      return {
        borderColor: 'rgba(22,163,74,0.35)',
        backgroundColor: 'rgba(22,163,74,0.08)',
        color: 'var(--color-success-500)',
      };
    case 'warning':
      return {
        borderColor: 'rgba(245,158,11,0.35)',
        backgroundColor: 'rgba(245,158,11,0.08)',
        color: 'var(--color-warning-500)',
      };
    case 'danger':
      return {
        borderColor: 'rgba(220,38,38,0.35)',
        backgroundColor: 'rgba(220,38,38,0.08)',
        color: 'var(--color-danger-500)',
      };
    default:
      return {
        borderColor: 'rgba(14,165,233,0.35)',
        backgroundColor: 'rgba(14,165,233,0.08)',
        color: 'var(--color-info-500)',
      };
  }
}

export function Alert({ variant = 'info', title, icon, className = '', children, ...props }: AlertProps) {
  return (
    <div
      role="alert"
      className={['border p-3', className].join(' ')}
      style={{ borderRadius: 'var(--radius-md)', ...getAlertStyles(variant) }}
      {...props}
    >
      <div className="flex items-start gap-2">
        {icon && <span className="mt-0.5">{icon}</span>}
        <div className="min-w-0">
          {title && <p className="text-sm font-semibold mb-1">{title}</p>}
          <div className="text-sm">{children}</div>
        </div>
      </div>
    </div>
  );
}

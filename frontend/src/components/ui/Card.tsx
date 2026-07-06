import type { HTMLAttributes, ReactNode } from 'react';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  footer?: ReactNode;
}

export function Card({ title, subtitle, footer, className = '', children, ...props }: CardProps) {
  return (
    <div
      className={['border p-4', className].join(' ')}
      style={{
        borderColor: 'var(--color-border)',
        backgroundColor: 'var(--color-surface)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-sm)',
      }}
      {...props}
    >
      {(title || subtitle) && (
        <header className="mb-4">
          {title && (
            <h3 className="text-base font-semibold" style={{ color: 'var(--color-text)' }}>
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
              {subtitle}
            </p>
          )}
        </header>
      )}

      <div>{children}</div>

      {footer && <footer className="mt-4">{footer}</footer>}
    </div>
  );
}

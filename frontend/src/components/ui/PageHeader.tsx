import type { ReactNode } from 'react';

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--color-text)' }}>
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 text-sm" style={{ color: 'var(--color-text-muted)' }}>
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}

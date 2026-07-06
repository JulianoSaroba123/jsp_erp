import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: ReactNode;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className="text-sm">
      <ol className="flex flex-wrap items-center gap-2">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={`${item.label}-${index}`} className="flex items-center gap-2">
              {index > 0 && <span style={{ color: 'var(--color-text-muted)' }}>/</span>}
              {item.href && !isLast ? (
                <Link
                  to={item.href}
                  className="inline-flex items-center gap-1 hover:underline"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  {item.icon}
                  {item.label}
                </Link>
              ) : (
                <span className="inline-flex items-center gap-1" style={{ color: 'var(--color-text)' }}>
                  {item.icon}
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

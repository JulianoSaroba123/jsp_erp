import type { ReactNode } from 'react';

export interface DashboardGridProps {
  children: ReactNode;
  columns?: 1 | 2 | 3 | 4;
}

const columnsClassMap = {
  1: 'grid-cols-1',
  2: 'grid-cols-1 md:grid-cols-2',
  3: 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3',
  4: 'grid-cols-1 md:grid-cols-2 xl:grid-cols-4',
};

export function DashboardGrid({ children, columns = 3 }: DashboardGridProps) {
  return <div className={`grid gap-4 ${columnsClassMap[columns]}`}>{children}</div>;
}

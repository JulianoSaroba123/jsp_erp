import type { ReactNode } from 'react';
import { Card, ErrorState, LoadingBlock } from '../ui';

export interface DashboardWidgetProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  footer?: ReactNode;
  loading?: boolean;
  error?: string | null;
  children?: ReactNode;
}

export function DashboardWidget({
  title,
  subtitle,
  actions,
  footer,
  loading = false,
  error,
  children,
}: DashboardWidgetProps) {
  if (loading) {
    return <LoadingBlock title={`Carregando ${title}`} description="Aguarde alguns instantes." />;
  }

  if (error) {
    return <ErrorState title={`Erro em ${title}`} description={error} />;
  }

  return (
    <Card title={title} subtitle={subtitle} footer={footer}>
      {actions && <div className="mb-3">{actions}</div>}
      {children}
    </Card>
  );
}

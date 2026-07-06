import type { ReactNode } from 'react';
import { Card } from './Card';

export interface SectionCardProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function SectionCard({ title, subtitle, actions, children }: SectionCardProps) {
  return (
    <Card
      title={title}
      subtitle={subtitle}
      footer={actions ? <div className="flex items-center justify-end gap-2">{actions}</div> : undefined}
    >
      {children}
    </Card>
  );
}

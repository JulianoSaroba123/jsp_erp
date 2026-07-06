import { DashboardWidget } from './DashboardWidget';
import { Skeleton } from '../ui';

export interface ActivityListPlaceholderProps {
  title?: string;
  subtitle?: string;
  items?: number;
}

export function ActivityListPlaceholder({
  title = 'Atividades Recentes',
  subtitle = 'Placeholder sem consumo real de endpoint',
  items = 5,
}: ActivityListPlaceholderProps) {
  return (
    <DashboardWidget title={title} subtitle={subtitle}>
      <ul className="space-y-3">
        {Array.from({ length: items }).map((_, index) => (
          <li
            key={index}
            className="border p-3"
            style={{
              borderColor: 'var(--color-border)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <Skeleton width="50%" height={12} className="mb-2" />
            <Skeleton width="80%" height={10} />
          </li>
        ))}
      </ul>
    </DashboardWidget>
  );
}

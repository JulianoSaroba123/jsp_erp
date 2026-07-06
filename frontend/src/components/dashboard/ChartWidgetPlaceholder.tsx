import { DashboardWidget } from './DashboardWidget';
import { Skeleton } from '../ui';

export interface ChartWidgetPlaceholderProps {
  title: string;
  subtitle?: string;
  height?: number;
}

export function ChartWidgetPlaceholder({
  title,
  subtitle = 'Placeholder para integracao futura com Recharts',
  height = 220,
}: ChartWidgetPlaceholderProps) {
  return (
    <DashboardWidget title={title} subtitle={subtitle}>
      <div
        className="border p-4"
        style={{
          borderColor: 'var(--color-border)',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--color-surface-muted)',
        }}
      >
        <div className="flex items-end gap-2" style={{ height }}>
          <Skeleton width="12%" height="45%" rounded="sm" />
          <Skeleton width="12%" height="70%" rounded="sm" />
          <Skeleton width="12%" height="55%" rounded="sm" />
          <Skeleton width="12%" height="80%" rounded="sm" />
          <Skeleton width="12%" height="62%" rounded="sm" />
          <Skeleton width="12%" height="50%" rounded="sm" />
        </div>
      </div>
    </DashboardWidget>
  );
}

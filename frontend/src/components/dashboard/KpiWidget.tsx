import { DashboardWidget } from './DashboardWidget';

export interface KpiWidgetProps {
  title: string;
  value: string | number;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  subtitle?: string;
}

function resolveTrendColor(direction: KpiWidgetProps['trendDirection']) {
  if (direction === 'up') {
    return 'var(--color-success-500)';
  }
  if (direction === 'down') {
    return 'var(--color-danger-500)';
  }
  return 'var(--color-text-muted)';
}

export function KpiWidget({ title, value, trend, trendDirection = 'neutral', subtitle }: KpiWidgetProps) {
  return (
    <DashboardWidget title={title} subtitle={subtitle}>
      <div className="flex items-end justify-between gap-3">
        <strong className="text-3xl" style={{ color: 'var(--color-text)' }}>
          {value}
        </strong>

        {trend && (
          <span className="text-sm font-semibold" style={{ color: resolveTrendColor(trendDirection) }}>
            {trend}
          </span>
        )}
      </div>
    </DashboardWidget>
  );
}

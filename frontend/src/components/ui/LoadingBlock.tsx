import { Spinner } from './Spinner';

export interface LoadingBlockProps {
  title?: string;
  description?: string;
}

export function LoadingBlock({ title = 'Carregando', description }: LoadingBlockProps) {
  return (
    <div
      className="w-full py-10 px-4 text-center border"
      style={{ borderColor: 'var(--color-border)', borderRadius: 'var(--radius-lg)' }}
    >
      <Spinner size={28} className="mx-auto" />
      <h3 className="mt-3 text-base font-semibold" style={{ color: 'var(--color-text)' }}>
        {title}
      </h3>
      {description && (
        <p className="mt-1 text-sm" style={{ color: 'var(--color-text-muted)' }}>
          {description}
        </p>
      )}
    </div>
  );
}

import type { HTMLAttributes } from 'react';

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: number;
}

export function Spinner({ size = 24, className = '', style, ...props }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Carregando"
      className={['inline-block animate-spin rounded-full border-2 border-solid border-transparent', className].join(' ')}
      style={{
        width: size,
        height: size,
        borderTopColor: 'var(--color-primary)',
        borderRightColor: 'var(--color-primary)',
        ...style,
      }}
      {...props}
    />
  );
}

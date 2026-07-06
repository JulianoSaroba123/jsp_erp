import type { HTMLAttributes } from 'react';

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  rounded?: 'sm' | 'md' | 'lg' | 'full';
}

const roundedClass = {
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  full: 'rounded-full',
};

export function Skeleton({
  width,
  height = 16,
  rounded = 'md',
  className = '',
  style,
  ...props
}: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={['animate-pulse', roundedClass[rounded], className].join(' ')}
      style={{
        width,
        height,
        backgroundColor: 'var(--color-surface-muted)',
        ...style,
      }}
      {...props}
    />
  );
}

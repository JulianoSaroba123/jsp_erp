import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-5 text-base',
};

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'text-white',
  secondary: 'border',
  ghost: 'border border-transparent',
  danger: 'text-white',
};

function getVariantInlineStyle(variant: ButtonVariant): React.CSSProperties {
  switch (variant) {
    case 'secondary':
      return {
        backgroundColor: 'var(--color-surface)',
        color: 'var(--color-text)',
        borderColor: 'var(--color-border)',
      };
    case 'ghost':
      return {
        backgroundColor: 'transparent',
        color: 'var(--color-text)',
      };
    case 'danger':
      return {
        backgroundColor: 'var(--color-danger-500)',
      };
    default:
      return {
        backgroundColor: 'var(--color-primary)',
      };
  }
}

export function Button({
  variant = 'primary',
  size = 'md',
  leftIcon,
  rightIcon,
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={[
        'inline-flex items-center justify-center gap-2 rounded-md font-medium',
        'transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-60',
        'focus-visible:outline-none',
        sizeStyles[size],
        variantStyles[variant],
        className,
      ].join(' ')}
      style={{
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-xs)',
        ...getVariantInlineStyle(variant),
      }}
      {...props}
    >
      {leftIcon}
      {children}
      {rightIcon}
    </button>
  );
}

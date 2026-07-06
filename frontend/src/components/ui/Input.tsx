import type { InputHTMLAttributes } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export function Input({ label, hint, error, className = '', id, ...props }: InputProps) {
  const inputId = id || props.name;

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium"
          style={{ color: 'var(--color-text)' }}
        >
          {label}
        </label>
      )}

      <input
        id={inputId}
        className={[
          'w-full h-10 px-3 border text-sm transition-colors',
          'placeholder:opacity-70 focus-visible:outline-none',
          className,
        ].join(' ')}
        style={{
          borderRadius: 'var(--radius-md)',
          borderColor: error ? 'var(--color-danger-500)' : 'var(--color-border)',
          backgroundColor: 'var(--color-surface)',
          color: 'var(--color-text)',
        }}
        {...props}
      />

      {error ? (
        <span className="text-xs" style={{ color: 'var(--color-danger-500)' }}>
          {error}
        </span>
      ) : (
        hint && (
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            {hint}
          </span>
        )
      )}
    </div>
  );
}

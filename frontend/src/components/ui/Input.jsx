import React, { useState } from 'react';

export function Input({ className = '', style = {}, ...props }) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <input
      className={className}
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid',
        borderColor: isFocused ? 'var(--accent-indigo)' : 'var(--border-focus)',
        borderRadius: 'var(--radius-sm)',
        padding: 'var(--space-2) var(--space-3)',
        color: 'var(--text-primary)',
        fontSize: '13px',
        outline: 'none',
        transition: 'all var(--transition-fast)',
        boxShadow: isFocused ? 'var(--shadow-glow)' : 'none',
        ...style
      }}
      onFocus={(e) => {
        setIsFocused(true);
        if (props.onFocus) props.onFocus(e);
      }}
      onBlur={(e) => {
        setIsFocused(false);
        if (props.onBlur) props.onBlur(e);
      }}
      {...props}
    />
  );
}

export function Select({ children, className = '', style = {}, ...props }) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <select
      className={className}
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid',
        borderColor: isFocused ? 'var(--accent-indigo)' : 'var(--border-focus)',
        borderRadius: 'var(--radius-sm)',
        padding: 'var(--space-2) var(--space-3)',
        color: 'var(--text-primary)',
        fontSize: '13px',
        outline: 'none',
        cursor: 'pointer',
        transition: 'all var(--transition-fast)',
        boxShadow: isFocused ? 'var(--shadow-glow)' : 'none',
        ...style
      }}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      {...props}
    >
      {children}
    </select>
  );
}

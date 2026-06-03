import React from 'react';

export function Card({ children, className = '', hoverable = false, ...props }) {
  const baseStyle = {
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--space-6)',
    transition: 'all var(--transition-normal)',
    boxShadow: 'var(--shadow-sm)',
  };

  return (
    <div
      className={className}
      style={{ ...baseStyle, ...props.style }}
      onMouseEnter={(e) => {
        if (hoverable) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = 'var(--shadow-md)';
          e.currentTarget.style.borderColor = 'var(--border-focus)';
        }
      }}
      onMouseLeave={(e) => {
        if (hoverable) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
          e.currentTarget.style.borderColor = 'var(--border-light)';
        }
      }}
      {...props}
    >
      {children}
    </div>
  );
}

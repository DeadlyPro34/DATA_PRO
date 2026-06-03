import React from 'react';

export function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className = '', 
  ...props 
}) {
  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    borderRadius: 'var(--radius-sm)',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
    border: '1px solid transparent',
    outline: 'none',
  };

  const variants = {
    primary: {
      background: 'var(--accent-indigo)',
      color: 'var(--text-inverse)',
      boxShadow: 'var(--shadow-glow)',
    },
    secondary: {
      background: 'var(--bg-surface-hover)',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-light)',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--text-secondary)',
    },
    danger: {
      background: 'rgba(255, 107, 107, 0.1)',
      color: '#ff6b6b',
      border: '1px solid rgba(255, 107, 107, 0.2)',
    }
  };

  const sizes = {
    sm: { padding: '4px 12px', fontSize: '11px' },
    md: { padding: '8px 16px', fontSize: '13px' },
    lg: { padding: '12px 24px', fontSize: '15px' },
    icon: { padding: '8px', fontSize: '16px' }
  };

  return (
    <button
      className={`btn-anim ${className}`}
      style={{
        ...baseStyle,
        ...variants[variant],
        ...sizes[size],
      }}
      onMouseEnter={(e) => {
        if (variant === 'primary') e.currentTarget.style.transform = 'translateY(-1px) scale(1.02)';
        else if (variant === 'secondary' || variant === 'danger') {
          e.currentTarget.style.transform = 'translateY(-1px)';
          e.currentTarget.style.borderColor = variant === 'danger' ? '#ff6b6b' : 'var(--accent-indigo)';
        }
        else if (variant === 'ghost') e.currentTarget.style.color = 'var(--text-primary)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0) scale(1)';
        if (variant === 'secondary' || variant === 'danger') {
          e.currentTarget.style.borderColor = variants[variant].border.split(' ')[2] || 'transparent';
        }
        else if (variant === 'ghost') e.currentTarget.style.color = 'var(--text-secondary)';
      }}
      onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.98)'}
      onMouseUp={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
      {...props}
    >
      {children}
    </button>
  );
}

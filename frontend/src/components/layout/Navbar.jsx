import React from 'react';
import { Database, TableProperties, BarChart3, Eraser, FolderOpen, BotMessageSquare, LayoutDashboard } from 'lucide-react';
import { Button } from '../ui/Button';

const TABS = [
  { id: 0, label: "Spreadsheet", icon: TableProperties },
  { id: 1, label: "Charts", icon: BarChart3 },
  { id: 2, label: "Data Cleaner", icon: Eraser },
  { id: 3, label: "Datasets", icon: FolderOpen },
  { id: 4, label: "AI Chat", icon: BotMessageSquare },
  { id: 5, label: "Auto Dashboard", icon: LayoutDashboard, accent: true },
];

export function Navbar({ activeTab, setActiveTab, onLogoClick, children }) {
  return (
    <nav className="glass-panel" style={{
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      {/* Logo & Brand */}
      <div 
        onClick={onLogoClick}
        style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        title="Go to Home"
      >
        <div style={{
          width: 36, height: 36, 
          background: 'var(--text-primary)',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-inverse)',
          boxShadow: '0 4px 12px rgba(15, 23, 42, 0.15)'
        }}>
          <Database size={20} strokeWidth={2.5} />
        </div>
        <div>
          <div style={{ fontSize: '16px', fontWeight: 800, letterSpacing: '1px', color: 'var(--text-primary)' }}>
            DATA PRO
          </div>
          <div style={{ fontSize: '10px', color: 'var(--accent-purple)', letterSpacing: '2px', fontWeight: 600 }}>
            FULL STACK EDITION
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px' }}>
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;
          const isAccent = tab.accent; // Auto Dashboard special tab
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                padding: '8px 16px',
                background: isActive
                  ? (isAccent ? 'linear-gradient(135deg,#4F46E5,#8B5CF6)' : 'var(--border-focus)')
                  : 'transparent',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                color: isActive ? (isAccent ? '#fff' : 'var(--accent-indigo)') : 'var(--text-secondary)',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
                outline: 'none',
                boxShadow: isActive && isAccent ? '0 4px 14px rgba(79,70,229,0.35)' : 'none',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = isAccent ? '#4F46E5' : 'var(--text-primary)';
                  e.currentTarget.style.background = isAccent ? 'rgba(79,70,229,0.08)' : 'var(--border-light)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = 'var(--text-secondary)';
                  e.currentTarget.style.background = 'transparent';
                }
              }}
              onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.96)'}
              onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
              <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* User Actions */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        {children}
      </div>
    </nav>
  );
}

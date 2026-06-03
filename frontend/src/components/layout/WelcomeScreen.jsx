import React from 'react';
import { Database, UploadCloud, FolderOpen, Sparkles } from 'lucide-react';
import { Card } from '../ui/Card';

export function WelcomeScreen({ onUploadClick, onDatasetsClick, onAiClick }) {
  return (
    <div className="animate-fade-in" style={{
      flex: 1, 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      background: 'transparent', 
      padding: 'var(--space-8)'
    }}>
      
      <div style={{
        width: 72, height: 72,
        background: 'linear-gradient(135deg, var(--accent-indigo), var(--accent-purple))',
        borderRadius: '24px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: '24px',
        boxShadow: 'var(--shadow-glow)',
        color: 'var(--text-inverse)'
      }}>
        <Database size={40} strokeWidth={2.5} />
      </div>

      <h1 style={{ fontSize: '42px', color: 'var(--text-primary)', marginBottom: '16px', textAlign: 'center', fontWeight: 800, letterSpacing: '-1px' }}>
        Welcome to DATA PRO
      </h1>
      
      <p style={{ fontSize: '16px', color: 'var(--text-secondary)', marginBottom: '48px', textAlign: 'center', maxWidth: '600px', lineHeight: 1.6 }}>
        Your professional AI-powered data assistant. Upload a dataset or select an existing one to start analyzing, cleaning, and visualizing your data.
      </p>
      
      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', justifyContent: 'center' }}>
        
        <Card hoverable onClick={onUploadClick} style={{ width: 240, textAlign: 'center', cursor: 'pointer', padding: '32px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px', color: 'var(--accent-indigo)' }}>
            <UploadCloud size={48} strokeWidth={1.5} />
          </div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
            Upload Dataset
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Excel, CSV, or JSON
          </div>
        </Card>

        <Card hoverable onClick={onDatasetsClick} style={{ width: 240, textAlign: 'center', cursor: 'pointer', padding: '32px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px', color: 'var(--accent-purple)' }}>
            <FolderOpen size={48} strokeWidth={1.5} />
          </div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
            My Datasets
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            View saved datasets
          </div>
        </Card>

        <Card hoverable onClick={onAiClick} style={{ width: 240, textAlign: 'center', cursor: 'pointer', padding: '32px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px', color: 'var(--accent-purple)' }}>
            <Sparkles size={48} strokeWidth={1.5} />
          </div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
            Ask AI Chat
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Analyze with Groq AI
          </div>
        </Card>

      </div>
    </div>
  );
}

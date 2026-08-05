import { Radio, RefreshCw } from 'lucide-react';

export function OfflineState({ title, description }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
        padding: '72px 24px',
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        textAlign: 'center',
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: 'var(--color-red-bg)',
          color: 'var(--color-red)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Radio size={26} strokeWidth={1.6} />
      </div>
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>
        {title || 'No fleet data available'}
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', maxWidth: 440, lineHeight: 1.6 }}>
        {description || 'Neither live nor historical fleet data is available right now. Start the DriveVitals backend and refresh to view fleet information.'}
      </div>
      <button
        onClick={() => window.location.reload()}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          marginTop: 6,
          padding: '8px 14px',
          borderRadius: 8,
          background: 'var(--color-accent)',
          color: '#fff',
          fontSize: 13,
          fontWeight: 600,
          border: 'none',
          cursor: 'pointer',
          transition: 'opacity 0.15s ease',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.85'; }}
        onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
      >
        <RefreshCw size={14} strokeWidth={2} />
        Retry
      </button>
    </div>
  );
}

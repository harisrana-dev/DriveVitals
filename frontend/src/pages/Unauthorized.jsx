import { ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function Unauthorized() {
  const navigate = useNavigate();

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 'calc(100vh - 160px)',
      textAlign: 'center',
      padding: 40,
    }}>
      <div style={{
        width: 72,
        height: 72,
        borderRadius: 16,
        background: 'var(--color-danger-subtle, rgba(220, 38, 38, 0.10))',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 20,
        color: 'var(--color-danger, #dc2626)',
      }}>
        <ShieldAlert size={36} strokeWidth={1.5} />
      </div>
      <h2 style={{
        fontSize: 20,
        fontWeight: 600,
        color: 'var(--color-text-primary)',
        marginBottom: 8,
      }}>
        Access denied
      </h2>
      <p style={{
        fontSize: 14,
        color: 'var(--color-text-secondary)',
        maxWidth: 380,
        lineHeight: 1.6,
        marginBottom: 24,
      }}>
        Your account does not have permission to view this page. If you
        believe this is a mistake, contact your fleet administrator.
      </p>
      <button
        onClick={() => navigate('/dashboard')}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 16px',
          borderRadius: 8,
          border: 'none',
          background: 'var(--color-accent)',
          color: '#fff',
          fontSize: 13,
          fontWeight: 500,
          cursor: 'pointer',
        }}
      >
        Back to dashboard
      </button>
    </div>
  );
}

export default Unauthorized;
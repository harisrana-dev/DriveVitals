export default function PagePlaceholder({ icon, title, description }) {
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
        background: 'var(--color-accent-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 20,
        color: 'var(--color-accent)',
      }}>
        {icon}
      </div>
      <h2 style={{
        fontSize: 20,
        fontWeight: 600,
        color: 'var(--color-text-primary)',
        marginBottom: 8,
      }}>
        {title}
      </h2>
      <p style={{
        fontSize: 14,
        color: 'var(--color-text-secondary)',
        maxWidth: 380,
        lineHeight: 1.6,
        marginBottom: 24,
      }}>
        {description}
      </p>
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 16px',
        borderRadius: 8,
        background: 'var(--color-accent-subtle)',
        color: 'var(--color-accent)',
        fontSize: 13,
        fontWeight: 500,
      }}>
        Module under development
      </div>
    </div>
  );
}

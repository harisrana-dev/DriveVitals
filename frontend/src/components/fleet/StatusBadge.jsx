const VARIANTS = {
  ACTIVE: {
    bg: 'var(--color-green-bg)',
    color: 'var(--color-green)',
    dot: true,
    label: 'ACTIVE',
  },
  IDLE: {
    bg: 'var(--color-amber-bg)',
    color: 'var(--color-amber)',
    dot: true,
    label: 'IDLE',
  },
  ALERT: {
    bg: 'var(--color-red-bg)',
    color: 'var(--color-red)',
    dot: false,
    label: 'ALERT',
  },
};

export function StatusBadge({ status, size = 'md' }) {
  const v = VARIANTS[status] || VARIANTS.ACTIVE;

  const sizeStyles = size === 'lg'
    ? { padding: '4px 12px', fontSize: 13, gap: 6, dotSize: 8 }
    : { padding: '2px 8px', fontSize: 11, gap: 4, dotSize: 6 };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: sizeStyles.gap,
        padding: sizeStyles.padding,
        borderRadius: 6,
        background: v.bg,
        color: v.color,
        fontSize: sizeStyles.fontSize,
        fontWeight: 600,
        letterSpacing: '0.02em',
        lineHeight: 1,
      }}
    >
      {v.dot ? (
        <span
          style={{
            width: sizeStyles.dotSize,
            height: sizeStyles.dotSize,
            borderRadius: '50%',
            background: v.color,
          }}
        />
      ) : (
        <span
          style={{
            width: 0,
            height: 0,
            borderLeft: `${sizeStyles.dotSize * 0.6}px solid ${v.color}`,
            borderTop: `${sizeStyles.dotSize * 0.35}px solid transparent`,
            borderBottom: `${sizeStyles.dotSize * 0.35}px solid transparent`,
          }}
        />
      )}
      {v.label}
    </span>
  );
}

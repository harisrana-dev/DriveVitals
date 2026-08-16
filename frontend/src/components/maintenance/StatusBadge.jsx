import { memo } from 'react';
import { MAINTENANCE_STATUS_META } from '../../utils/maintenance';

export const StatusBadge = memo(function StatusBadge({ status, size = 'sm' }) {
  const meta = MAINTENANCE_STATUS_META[status] || {
    label: status || 'Unknown',
    color: 'var(--color-text-muted)',
    bg: 'var(--color-surface-hover)',
  };
  const fontSize = size === 'sm' ? 10 : 11;
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 4,
        background: meta.bg,
        color: meta.color,
        fontSize,
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        lineHeight: 1.4,
      }}
    >
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: meta.color, flexShrink: 0 }} />
      {meta.label}
    </span>
  );
});

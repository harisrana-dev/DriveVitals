import { memo } from 'react';

const STATUS_STYLE = {
  active: { color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  acknowledged: { color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  resolved: { color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' },
};

export const AlertStatusBadge = memo(function AlertStatusBadge({ status, size }) {
  const ss = STATUS_STYLE[status] || STATUS_STYLE.active;
  const fontS = size === 'sm' ? 10 : 11;
  const pad = size === 'sm' ? '2px 8px' : '3px 10px';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: pad,
        borderRadius: 4,
        background: ss.bg,
        color: ss.color,
        fontSize: fontS,
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.03em',
        lineHeight: 1,
      }}
    >
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: ss.color, flexShrink: 0 }} />
      {status}
    </span>
  );
});

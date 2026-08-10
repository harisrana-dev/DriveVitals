import { memo } from 'react';
import { tripStatusMeta } from '../../utils/trips';

export const TripStatusBadge = memo(function TripStatusBadge({ status, size = 'sm' }) {
  const meta = tripStatusMeta(status);
  if (!meta) return null;

  const isMd = size === 'md';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: isMd ? '3px 9px' : '2px 7px',
        borderRadius: 20,
        background: meta.bg,
        color: meta.color,
        fontSize: isMd ? 10 : 9,
        fontWeight: 700,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        whiteSpace: 'nowrap',
        lineHeight: 1.4,
        flexShrink: 0,
      }}
    >
      {meta.pulse && (
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: meta.color,
            animation: 'pulse-dot 2s infinite',
            flexShrink: 0,
          }}
        />
      )}
      {meta.label}
    </span>
  );
});

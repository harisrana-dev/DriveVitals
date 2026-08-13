import { memo } from 'react';

const VARIANTS = {
  low: { label: 'Low Risk', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  moderate: { label: 'Moderate', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  high: { label: 'High Risk', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  critical: { label: 'Critical', color: '#fff', bg: 'var(--color-red)' },
  unknown: { label: 'No Score', color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' },
};

export const DriverRiskBadge = memo(function DriverRiskBadge({ level, size = 'md' }) {
  const v = VARIANTS[level] || VARIANTS.unknown;
  const isCompact = size === 'sm';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: isCompact ? 4 : 6,
        padding: isCompact ? '2px 8px' : '4px 12px',
        borderRadius: 6,
        background: v.bg,
        color: v.color,
        fontSize: isCompact ? 11 : 12,
        fontWeight: 600,
        letterSpacing: '0.02em',
        lineHeight: 1,
        whiteSpace: 'nowrap',
      }}
    >
      <span
        style={{
          width: isCompact ? 5 : 7,
          height: isCompact ? 5 : 7,
          borderRadius: '50%',
          background: v.color,
          flexShrink: 0,
        }}
      />
      {v.label}
    </span>
  );
});

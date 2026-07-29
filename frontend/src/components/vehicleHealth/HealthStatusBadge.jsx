import { memo } from 'react';
import { healthColor, healthBg } from '../../utils/health';

const LABELS = {
  healthy: 'Healthy',
  warning: 'Warning',
  critical: 'Critical',
};

export const HealthStatusBadge = memo(function HealthStatusBadge({ category, size }) {
  const color = healthColor(category);
  const bg = healthBg(category);
  const label = LABELS[category] || category;
  const fontS = size === 'sm' ? 10 : 11;
  const pad = size === 'sm' ? '2px 8px' : '3px 10px';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: pad,
        borderRadius: 6,
        background: bg,
        color,
        fontSize: fontS,
        fontWeight: 600,
        letterSpacing: '0.02em',
        lineHeight: 1,
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: color,
          flexShrink: 0,
        }}
      />
      {label}
    </span>
  );
});

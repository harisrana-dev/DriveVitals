import { memo } from 'react';
import { healthCategory, healthColor, healthBg } from '../../utils/health';

const LABELS = { healthy: 'Good', warning: 'Fair', critical: 'Poor' };

export const MaintenanceHealthBadge = memo(function MaintenanceHealthBadge({ score }) {
  const cat = healthCategory(score);
  const color = healthColor(cat);
  const bg = healthBg(cat);
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '2px 8px',
        borderRadius: 4,
        background: bg,
        color,
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '0.02em',
        lineHeight: 1.4,
      }}
    >
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: color, flexShrink: 0 }} />
      {LABELS[cat] || cat}
    </span>
  );
});

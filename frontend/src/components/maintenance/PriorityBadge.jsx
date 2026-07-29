import { memo } from 'react';
import { priorityStyle } from '../../utils/maintenance';

const LABELS = { critical: 'Critical', due: 'Due Soon', good: 'Good' };

export const PriorityBadge = memo(function PriorityBadge({ priority }) {
  const ps = priorityStyle(priority);
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 4,
        background: ps.bg,
        color: ps.color,
        fontSize: 10,
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        lineHeight: 1.4,
      }}
    >
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: ps.color, flexShrink: 0 }} />
      {LABELS[priority] || priority}
    </span>
  );
});

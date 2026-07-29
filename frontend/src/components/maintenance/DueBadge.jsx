import { memo } from 'react';
import { dueStatusStyle } from '../../utils/maintenance';

export const DueBadge = memo(function DueBadge({ status }) {
  const ds = dueStatusStyle(status);
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 4,
        background: ds.bg,
        color: ds.color,
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '0.03em',
        lineHeight: 1.4,
      }}
    >
      {status}
    </span>
  );
});

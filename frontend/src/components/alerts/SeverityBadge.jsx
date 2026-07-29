import { memo } from 'react';
import { severityColor, severityBg, severityLabel } from '../../utils/alerts';

export const SeverityBadge = memo(function SeverityBadge({ severity, size }) {
  const color = severityColor(severity);
  const bg = severityBg(severity);
  const label = severityLabel(severity);
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
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: color, flexShrink: 0 }} />
      {label}
    </span>
  );
});

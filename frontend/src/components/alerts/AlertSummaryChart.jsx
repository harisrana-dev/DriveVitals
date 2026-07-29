import { memo } from 'react';
import { useAlerts } from '../../hooks/useAlerts';

export const AlertSummaryChart = memo(function AlertSummaryChart() {
  const { distribution } = useAlerts();
  const total = distribution.reduce((s, d) => s + d.count, 0);

  if (total === 0) return null;

  const size = 180;
  const stroke = 24;
  const radius = (size - stroke) / 2;
  const circ = 2 * Math.PI * radius;

  let offset = 0;
  const slices = distribution.map((seg) => {
    const pct = total > 0 ? seg.count / total : 0;
    const len = pct * circ;
    const dash = len > 0 ? `${len} ${circ - len}` : `0 ${circ}`;
    const dashOffset = -offset;
    offset += len;
    return { ...seg, pct, dash, dashOffset };
  });

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 16 }}>
        Alert Summary
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--color-border-light)"
            strokeWidth={stroke}
          />
          {slices.map((s) =>
            s.count > 0 ? (
              <circle
                key={s.key}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={s.color}
                strokeWidth={stroke}
                strokeDasharray={s.dash}
                strokeDashoffset={s.dashOffset}
                strokeLinecap="butt"
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
                style={{ transition: 'stroke-dasharray 0.5s ease, stroke-dashoffset 0.5s ease' }}
              />
            ) : null
          )}
          <text
            x={size / 2}
            y={size / 2 + 5}
            textAnchor="middle"
            fontSize="22"
            fontWeight="700"
            fill="var(--color-text-primary)"
            fontFamily="inherit"
          >
            {total}
          </text>
          <text
            x={size / 2}
            y={size / 2 + 22}
            textAnchor="middle"
            fontSize="10"
            fill="var(--color-text-muted)"
            fontFamily="inherit"
          >
            total
          </text>
        </svg>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
          {slices.map((s) => (
            <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 3,
                  background: s.color,
                  flexShrink: 0,
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  {s.label}
                </div>
              </div>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
                {s.count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

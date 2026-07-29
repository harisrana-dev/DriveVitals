import { memo } from 'react';
import { useVehicleHealth } from '../../hooks/useVehicleHealth';

const SEGMENTS = [
  { key: 'healthy', label: 'Healthy', color: 'var(--color-green)' },
  { key: 'warning', label: 'Warning', color: 'var(--color-amber)' },
  { key: 'critical', label: 'Critical', color: 'var(--color-red)' },
];

export const HealthDistribution = memo(function HealthDistribution() {
  const { fleetStats } = useVehicleHealth();

  if (!fleetStats || fleetStats.total === 0) return null;

  const total = fleetStats.total;
  const size = 180;
  const stroke = 24;
  const radius = (size - stroke) / 2;
  const circ = 2 * Math.PI * radius;

  let offset = 0;
  const slices = SEGMENTS.map((seg) => {
    const count = fleetStats[`${seg.key}Count`] ?? 0;
    const pct = total > 0 ? count / total : 0;
    const len = pct * circ;
    const dash = len > 0 ? `${len} ${circ - len}` : `0 ${circ}`;
    const dashOffset = -offset;
    offset += len;
    return { ...seg, count, pct, dash, dashOffset };
  });

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
        Health Distribution
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 24,
        }}
      >
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
            y={size / 2 - 4}
            textAnchor="middle"
            fontSize="22"
            fontWeight="700"
            fill="var(--color-text-primary)"
            fontFamily="inherit"
          >
            {fleetStats.avgScore}
          </text>
          <text
            x={size / 2}
            y={size / 2 + 14}
            textAnchor="middle"
            fontSize="10"
            fill="var(--color-text-muted)"
            fontFamily="inherit"
          >
            avg score
          </text>
        </svg>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          {slices.map((s) => (
            <div
              key={s.key}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 3,
                  background: s.color,
                  flexShrink: 0,
                }}
              />
              <div>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: 'var(--color-text-primary)',
                    fontVariantNumeric: 'tabular-nums',
                  }}
                >
                  {s.count}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--color-text-muted)',
                  }}
                >
                  {s.label}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

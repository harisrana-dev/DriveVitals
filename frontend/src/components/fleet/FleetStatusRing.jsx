import { memo } from 'react';
import { useVehicles } from '../../hooks/useFleetData';

const SEGMENTS = [
  { key: 'ACTIVE', color: '#22C55E', label: 'Active' },
  { key: 'ALERT', color: '#EF4444', label: 'Alert' },
  { key: 'MAINTENANCE', color: '#3B82F6', label: 'Maintenance' },
  { key: 'TRIP_COMPLETED', color: '#A855F7', label: 'Trip Completed' },
  { key: 'IDLE', color: '#FACC15', label: 'Idle' },
  { key: 'OFFLINE', color: '#6B7280', label: 'Offline' },
];

const SIZE = 100;
const STROKE = 8;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export const FleetStatusRing = memo(function FleetStatusRing() {
  const vehicles = useVehicles();

  const counts = { ACTIVE: 0, ALERT: 0, MAINTENANCE: 0, TRIP_COMPLETED: 0, IDLE: 0, OFFLINE: 0 };
  vehicles.forEach((v) => {
    counts[v.displayStatus] = (counts[v.displayStatus] || 0) + 1;
  });

  const total = Object.values(counts).reduce((sum, n) => sum + n, 0);
  if (total === 0) return null;

  let offset = 0;
  const slices = SEGMENTS.map((seg) => {
    const pct = counts[seg.key] / total;
    const length = pct * CIRCUMFERENCE;
    const dash = `${length} ${CIRCUMFERENCE - length}`;
    const dashOffset = -offset;
    offset += length;
    return { ...seg, pct, length, dash, dashOffset };
  });

  return (
    <div
      className="fade-in stagger-3"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 24,
      }}
    >
      <div style={{ position: 'relative', width: SIZE, height: SIZE, flexShrink: 0 }}>
        <svg width={SIZE} height={SIZE} style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke="var(--color-border-light)"
            strokeWidth={STROKE}
          />
          {slices.map((seg) =>
            seg.pct > 0 ? (
              <circle
                key={seg.key}
                cx={SIZE / 2}
                cy={SIZE / 2}
                r={RADIUS}
                fill="none"
                stroke={seg.color}
                strokeWidth={STROKE}
                strokeDasharray={seg.dash}
                strokeDashoffset={seg.dashOffset}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 0.5s ease' }}
              />
            ) : null
          )}
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-primary)', lineHeight: 1 }}>
            {total}
          </span>
          <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>Total</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
          Fleet Distribution
        </div>
        {SEGMENTS.map((seg) => {
          const pct = total > 0 ? Math.round((counts[seg.key] / total) * 100) : 0;
          return (
            <div key={seg.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 2,
                  background: seg.color,
                  flexShrink: 0,
                }}
              />
              <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', flex: 1 }}>
                {seg.label}
              </span>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums', minWidth: 24, textAlign: 'right' }}>
                {counts[seg.key]}
              </span>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums', minWidth: 36, textAlign: 'right' }}>
                {pct}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
});

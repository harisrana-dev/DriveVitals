import { memo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const SEVERITY_COLORS = {
  severe: 'var(--color-red)',
  moderate: 'var(--color-amber)',
  minor: 'var(--color-text-muted)',
  none: 'var(--color-text-muted)',
};

const SEVERITY_BG = {
  severe: 'var(--color-red-bg)',
  moderate: 'var(--color-amber-bg)',
  minor: 'transparent',
  none: 'transparent',
};

const TREND_LABELS = {
  improving: { label: 'Improving', icon: TrendingUp, color: 'var(--color-green)' },
  stable: { label: 'Stable', icon: Minus, color: 'var(--color-text-muted)' },
  declining: { label: 'Declining', icon: TrendingDown, color: 'var(--color-red)' },
};

function TrendIndicator({ trend }) {
  const t = TREND_LABELS[trend] || TREND_LABELS.stable;
  const Icon = t.icon;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: t.color, fontWeight: 500 }}>
      <Icon size={12} strokeWidth={2} />
      {t.label}
    </div>
  );
}

export const DriverBehaviourTimeline = memo(function DriverBehaviourTimeline({ driver }) {
  const behaviours = [
    { label: 'Harsh Braking', count: driver.harshBraking.count, severity: driver.harshBraking.severity, trend: driver.harshBraking.trend },
    { label: 'Aggressive Acceleration', count: driver.aggressiveAcceleration.count, severity: driver.aggressiveAcceleration.severity, trend: driver.aggressiveAcceleration.trend },
    { label: 'Overspeed Events', count: driver.overspeedEvents.count, severity: driver.overspeedEvents.severity, trend: driver.overspeedEvents.trend },
    { label: 'High RPM Events', count: driver.highRpmEvents.count, severity: driver.highRpmEvents.severity, trend: driver.highRpmEvents.trend },
  ];

  return (
    <div>
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          marginBottom: 10,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        Behaviour Analysis
      </div>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        {behaviours.map((b) => (
          <div
            key={b.label}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 48px 1fr',
              gap: 8,
              alignItems: 'center',
              padding: '10px 12px',
              borderRadius: 8,
              background: b.count > 0 ? SEVERITY_BG[b.severity] : 'var(--color-bg)',
              border: `1px solid ${b.count > 0 ? (SEVERITY_COLORS[b.severity] || 'var(--color-border-light)') : 'var(--color-border-light)'}`,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: 'var(--color-text-primary)',
                }}
              >
                {b.label}
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--color-text-muted)',
                  textTransform: 'capitalize',
                }}
              >
                {b.severity}
              </div>
            </div>
            <div
              style={{
                textAlign: 'center',
                fontSize: 22,
                fontWeight: 700,
                color: SEVERITY_COLORS[b.severity],
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {b.count}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <TrendIndicator trend={b.trend} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

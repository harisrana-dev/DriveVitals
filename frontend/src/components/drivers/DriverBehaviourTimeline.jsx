import { memo } from 'react';

const SEVERITY_COLORS = {
  severe: 'var(--color-red)',
  moderate: 'var(--color-amber)',
  none: 'var(--color-text-muted)',
};

const SEVERITY_BG = {
  severe: 'var(--color-red-bg)',
  moderate: 'var(--color-amber-bg)',
  none: 'transparent',
};

export const DriverBehaviourTimeline = memo(function DriverBehaviourTimeline({ driver }) {
  const behaviour = driver.behaviour || {};
  const behaviours = [
    { label: 'Harsh Braking', count: behaviour.harshBraking?.count ?? 0, rate: behaviour.harshBraking?.ratePer100Km, severity: behaviour.harshBraking?.severity || 'none' },
    { label: 'Aggressive Acceleration', count: behaviour.aggressiveAcceleration?.count ?? 0, rate: behaviour.aggressiveAcceleration?.ratePer100Km, severity: behaviour.aggressiveAcceleration?.severity || 'none' },
    { label: 'Overspeed Events', count: behaviour.overspeedEvents?.count ?? 0, rate: behaviour.overspeedEvents?.ratePer100Km, severity: behaviour.overspeedEvents?.severity || 'none' },
    { label: 'High RPM Events', count: behaviour.highRpmEvents?.count ?? 0, rate: behaviour.highRpmEvents?.ratePer100Km, severity: behaviour.highRpmEvents?.severity || 'none' },
  ];

  return (
    <div>
      <SectionTitle>Behaviour Analysis</SectionTitle>
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
              gridTemplateColumns: '1fr 48px',
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
                {b.count > 0
                  ? `${b.severity}${b.rate != null ? ` · ${b.rate} per 100 km` : ''}`
                  : 'No events recorded'}
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
          </div>
        ))}
      </div>
    </div>
  );
});

function SectionTitle({ children }) {
  return (
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
      {children}
    </div>
  );
}

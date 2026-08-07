import { memo } from 'react';
import { Route, Map, Shield, Fuel } from 'lucide-react';
import { useTripsSummary } from '../../hooks/useTripsData';

export const TripsKpis = memo(function TripsKpis() {
  const summary = useTripsSummary();

  const cards = [
    {
      label: 'Total Trips',
      value: summary.totalTrips,
      icon: <Route size={18} strokeWidth={1.8} />,
      color: 'var(--color-accent)',
      bgColor: 'var(--color-accent-subtle)',
      suffix: '',
    },
    {
      label: 'Total Distance',
      value: summary.totalDistance.toFixed(1),
      icon: <Map size={18} strokeWidth={1.8} />,
      color: 'var(--color-green)',
      bgColor: 'var(--color-green-bg)',
      suffix: ' km',
    },
    {
      label: 'Avg Safety Score',
      value: Math.round(summary.avgSafetyScore),
      icon: <Shield size={18} strokeWidth={1.8} />,
      color: summary.avgSafetyScore >= 80 ? 'var(--color-green)' : summary.avgSafetyScore >= 60 ? 'var(--color-amber)' : 'var(--color-red)',
      bgColor: summary.avgSafetyScore >= 80 ? 'var(--color-green-bg)' : summary.avgSafetyScore >= 60 ? 'var(--color-amber-bg)' : 'var(--color-red-bg)',
      suffix: '%',
    },
    {
      label: 'Total Fuel',
      value: summary.totalFuel.toFixed(1),
      icon: <Fuel size={18} strokeWidth={1.8} />,
      color: 'var(--color-amber)',
      bgColor: 'var(--color-amber-bg)',
      suffix: ' L',
    },
  ];

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 12,
      }}
    >
      {cards.map((card, i) => (
        <div
          key={card.label}
          className={`fade-in stagger-${i + 1}`}
          style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 12,
            padding: '16px 18px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 14,
            transition: 'border-color 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = card.color; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
        >
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              background: card.bgColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: card.color,
              flexShrink: 0,
            }}
          >
            {card.icon}
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>
              {card.label}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
              <span
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: 'var(--color-text-primary)',
                  lineHeight: 1,
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {card.value}
              </span>
              {card.suffix && (
                <span style={{ fontSize: 13, color: 'var(--color-text-muted)', fontWeight: 400 }}>
                  {card.suffix}
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
});

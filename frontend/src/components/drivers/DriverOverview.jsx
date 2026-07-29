import { memo } from 'react';
import { Users, Shield, AlertTriangle, Activity } from 'lucide-react';
import { useDriversOverview } from '../../hooks/useDrivers';
import { useSmoothValue } from '../../hooks/useSmoothValue';

export const DriverOverview = memo(function DriverOverview() {
  const overview = useDriversOverview();

  const smoothScore = useSmoothValue(overview.avgScore);

  const cards = [
    {
      label: 'Total Drivers',
      value: overview.total,
      icon: <Users size={18} strokeWidth={1.8} />,
      color: 'var(--color-accent)',
      bgColor: 'var(--color-accent-subtle)',
      suffix: '',
    },
    {
      label: 'Average Safety Score',
      value: smoothScore,
      icon: <Shield size={18} strokeWidth={1.8} />,
      color: smoothScore >= 80 ? 'var(--color-green)' : smoothScore >= 60 ? 'var(--color-amber)' : 'var(--color-red)',
      bgColor: smoothScore >= 80 ? 'var(--color-green-bg)' : smoothScore >= 60 ? 'var(--color-amber-bg)' : 'var(--color-red-bg)',
      suffix: '/100',
    },
    {
      label: 'High Risk Drivers',
      value: overview.highRisk,
      icon: <AlertTriangle size={18} strokeWidth={1.8} />,
      color: overview.highRisk > 0 ? 'var(--color-red)' : 'var(--color-green)',
      bgColor: overview.highRisk > 0 ? 'var(--color-red-bg)' : 'var(--color-green-bg)',
      suffix: '',
    },
    {
      label: 'Active Drivers Now',
      value: overview.active,
      icon: <Activity size={18} strokeWidth={1.8} />,
      color: 'var(--color-green)',
      bgColor: 'var(--color-green-bg)',
      suffix: '',
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
                {typeof card.value === 'number' ? Math.round(card.value) : card.value}
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

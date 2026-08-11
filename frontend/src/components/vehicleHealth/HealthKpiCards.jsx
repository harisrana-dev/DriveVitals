import { memo } from 'react';
import { Activity, Shield, AlertTriangle, HeartPulse } from 'lucide-react';
import { useVehicleHealth } from '../../hooks/useVehicleHealth';
import { useSmoothValue } from '../../hooks/useSmoothValue';

export const HealthKpiCards = memo(function HealthKpiCards() {
  const { fleetStats } = useVehicleHealth();
  const hasAvg = fleetStats?.avgScore != null;
  const safeAvg = hasAvg ? fleetStats.avgScore : 0;
  const smoothFleetHealth = useSmoothValue(safeAvg);
  const displayedAvg = hasAvg ? Math.round(smoothFleetHealth) : '\u2014';

  const cards = [
    {
      label: 'Fleet Health Score',
      value: displayedAvg,
      icon: <HeartPulse size={18} strokeWidth={1.8} />,
      color: !hasAvg ? 'var(--color-text-muted)' : smoothFleetHealth >= 90 ? 'var(--color-green)' : smoothFleetHealth >= 70 ? 'var(--color-amber)' : 'var(--color-red)',
      bgColor: !hasAvg ? 'var(--color-surface-hover)' : smoothFleetHealth >= 90 ? 'var(--color-green-bg)' : smoothFleetHealth >= 70 ? 'var(--color-amber-bg)' : 'var(--color-red-bg)',
      suffix: hasAvg ? '%' : '',
    },
    {
      label: 'Healthy Vehicles',
      value: fleetStats?.healthyCount ?? 0,
      icon: <Shield size={18} strokeWidth={1.8} />,
      color: 'var(--color-green)',
      bgColor: 'var(--color-green-bg)',
      suffix: fleetStats ? `/ ${fleetStats.total}` : '',
    },
    {
      label: 'Attention Required',
      value: fleetStats?.warningCount ?? 0,
      icon: <AlertTriangle size={18} strokeWidth={1.8} />,
      color: (fleetStats?.warningCount ?? 0) > 0 ? 'var(--color-amber)' : 'var(--color-text-muted)',
      bgColor: (fleetStats?.warningCount ?? 0) > 0 ? 'var(--color-amber-bg)' : 'var(--color-bg)',
      suffix: '',
    },
    {
      label: 'Critical Issues',
      value: fleetStats?.criticalCount ?? 0,
      icon: <Activity size={18} strokeWidth={1.8} />,
      color: (fleetStats?.criticalCount ?? 0) > 0 ? 'var(--color-red)' : 'var(--color-text-muted)',
      bgColor: (fleetStats?.criticalCount ?? 0) > 0 ? 'var(--color-red-bg)' : 'var(--color-bg)',
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

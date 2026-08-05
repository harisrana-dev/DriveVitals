import { memo } from 'react';
import { Truck, Activity, Power, AlertTriangle } from 'lucide-react';
import { useDashboardSummary } from '../../hooks/useFleetData';
import { useVehicles } from '../../hooks/useFleetData';

export const FleetSummary = memo(function FleetSummary() {
  const summary = useDashboardSummary();
  const vehicles = useVehicles();

  const idleCount = vehicles.filter((v) => v.displayStatus === 'IDLE').length;

  const cards = [
    {
      label: 'Total Vehicles',
      value: summary.totalVehicles,
      icon: <Truck size={18} strokeWidth={1.8} />,
      color: 'var(--color-accent)',
      bgColor: 'var(--color-accent-subtle)',
    },
    {
      label: 'Active',
      value: summary.activeVehicles,
      icon: <Activity size={18} strokeWidth={1.8} />,
      color: 'var(--color-green)',
      bgColor: 'var(--color-green-bg)',
    },
    {
      label: 'Idle',
      value: idleCount,
      icon: <Power size={18} strokeWidth={1.8} />,
      color: 'var(--color-amber)',
      bgColor: 'var(--color-amber-bg)',
    },
    {
      label: 'Needs Attention',
      value: summary.attentionRequired,
      icon: <AlertTriangle size={18} strokeWidth={1.8} />,
      color: summary.attentionRequired > 0 ? 'var(--color-red)' : 'var(--color-green)',
      bgColor: summary.attentionRequired > 0 ? 'var(--color-red-bg)' : 'var(--color-green-bg)',
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
                }}
              >
                {card.value}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
});

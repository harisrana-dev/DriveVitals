import { memo } from 'react';
import { Truck, Activity, HeartPulse, AlertTriangle } from 'lucide-react';
import { useDashboardSummary } from '../../hooks/useFleetData';

export const KpiCards = memo(function KpiCards() {
  const summary = useDashboardSummary();

  const cards = [
    {
      label: 'Total Fleet',
      value: summary.totalVehicles,
      unit: 'vehicles',
      icon: <Truck size={18} strokeWidth={1.8} />,
      color: 'var(--color-accent)',
      bgColor: 'var(--color-accent-subtle)',
    },
    {
      label: 'Active Now',
      value: summary.activeVehicles,
      unit: `${summary.totalVehicles > 0 ? Math.round((summary.activeVehicles / summary.totalVehicles) * 100) : 0}% of fleet`,
      icon: <Activity size={18} strokeWidth={1.8} />,
      color: 'var(--color-green)',
      bgColor: 'var(--color-green-bg)',
    },
    {
      label: 'Fleet Health',
      value: summary.fleetHealthScore,
      unit: summary.fleetHealthScore >= 80 ? 'Healthy' : 'Needs attention',
      icon: <HeartPulse size={18} strokeWidth={1.8} />,
      color: summary.fleetHealthScore >= 80 ? 'var(--color-green)' : 'var(--color-amber)',
      bgColor: summary.fleetHealthScore >= 80 ? 'var(--color-green-bg)' : 'var(--color-amber-bg)',
      suffix: ' / 100',
    },
    {
      label: 'Needs Attention',
      value: summary.attentionRequired,
      unit: 'Review required',
      icon: <AlertTriangle size={18} strokeWidth={1.8} />,
      color: summary.attentionRequired > 0 ? 'var(--color-amber)' : 'var(--color-green)',
      bgColor: summary.attentionRequired > 0 ? 'var(--color-amber-bg)' : 'var(--color-green-bg)',
    },
  ];

  return (
    <div className="kpi-grid">
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
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = card.color;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-border)';
          }}
        >
          <div style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: card.bgColor,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: card.color,
            flexShrink: 0,
          }}>
            {card.icon}
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>
              {card.label}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
              <span style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary)', lineHeight: 1 }}>
                {card.value}
              </span>
              {card.suffix && (
                <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>{card.suffix}</span>
              )}
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 4 }}>
              {card.unit}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
});

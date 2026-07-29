import { memo } from 'react';
import { Wrench, AlertTriangle, CalendarRange, ShieldCheck } from 'lucide-react';
import { useMaintenance } from '../../hooks/useMaintenance';
import { useSmoothValue } from '../../hooks/useSmoothValue';

export const MaintenanceKpiCards = memo(function MaintenanceKpiCards() {
  const { kpiStats } = useMaintenance();
  const smoothRequires = useSmoothValue(kpiStats?.requiresService ?? 0);
  const smoothOverdue = useSmoothValue(kpiStats?.overdue ?? 0);
  const smoothUpcoming = useSmoothValue(kpiStats?.upcoming ?? 0);
  const smoothCompliance = useSmoothValue(kpiStats?.compliancePct ?? 0);

  const cards = [
    {
      label: 'Requires Service',
      value: Math.round(smoothRequires),
      icon: <Wrench size={18} strokeWidth={1.8} />,
      color: smoothRequires > 0 ? 'var(--color-amber)' : 'var(--color-green)',
      bgColor: smoothRequires > 0 ? 'var(--color-amber-bg)' : 'var(--color-green-bg)',
    },
    {
      label: 'Overdue Services',
      value: Math.round(smoothOverdue),
      icon: <AlertTriangle size={18} strokeWidth={1.8} />,
      color: smoothOverdue > 0 ? 'var(--color-red)' : 'var(--color-green)',
      bgColor: smoothOverdue > 0 ? 'var(--color-red-bg)' : 'var(--color-green-bg)',
    },
    {
      label: 'Upcoming (30 days)',
      value: Math.round(smoothUpcoming),
      icon: <CalendarRange size={18} strokeWidth={1.8} />,
      color: 'var(--color-accent)',
      bgColor: 'var(--color-accent-subtle)',
    },
    {
      label: 'Compliance',
      value: Math.round(smoothCompliance),
      icon: <ShieldCheck size={18} strokeWidth={1.8} />,
      color: smoothCompliance >= 80 ? 'var(--color-green)' : smoothCompliance >= 50 ? 'var(--color-amber)' : 'var(--color-red)',
      bgColor: smoothCompliance >= 80 ? 'var(--color-green-bg)' : smoothCompliance >= 50 ? 'var(--color-amber-bg)' : 'var(--color-red-bg)',
      suffix: '%',
    },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
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

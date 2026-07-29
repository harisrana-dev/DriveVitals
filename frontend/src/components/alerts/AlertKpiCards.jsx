import { memo } from 'react';
import { AlertTriangle, Bell, CheckCircle, Clock } from 'lucide-react';
import { useAlerts } from '../../hooks/useAlerts';
import { useSmoothValue } from '../../hooks/useSmoothValue';

export const AlertKpiCards = memo(function AlertKpiCards() {
  const { kpis } = useAlerts();
  const smoothCritical = useSmoothValue(kpis?.critical ?? 0);
  const smoothActive = useSmoothValue(kpis?.active ?? 0);
  const smoothAcknowledged = useSmoothValue(kpis?.acknowledged ?? 0);
  const smoothResponse = useSmoothValue(kpis?.responseTime ?? 0);

  const cards = [
    {
      label: 'Critical Alerts',
      value: Math.round(smoothCritical),
      icon: <AlertTriangle size={18} strokeWidth={1.8} />,
      color: smoothCritical > 0 ? 'var(--color-red)' : 'var(--color-green)',
      bgColor: smoothCritical > 0 ? 'var(--color-red-bg)' : 'var(--color-green-bg)',
    },
    {
      label: 'Active Alerts',
      value: Math.round(smoothActive),
      icon: <Bell size={18} strokeWidth={1.8} />,
      color: smoothActive > 0 ? 'var(--color-amber)' : 'var(--color-green)',
      bgColor: smoothActive > 0 ? 'var(--color-amber-bg)' : 'var(--color-green-bg)',
    },
    {
      label: 'Acknowledged Today',
      value: Math.round(smoothAcknowledged),
      icon: <CheckCircle size={18} strokeWidth={1.8} />,
      color: 'var(--color-accent)',
      bgColor: 'var(--color-accent-subtle)',
    },
    {
      label: 'Avg Response Time',
      value: Math.round(smoothResponse),
      icon: <Clock size={18} strokeWidth={1.8} />,
      color: 'var(--color-text-primary)',
      bgColor: 'var(--color-surface-hover)',
      suffix: 'min',
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

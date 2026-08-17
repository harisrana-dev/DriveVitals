import { memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Truck, Activity, HeartPulse, AlertTriangle } from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';
import { canonicalHealthCategory, healthColor, healthLabel } from '../../utils/health';

/**
 * KPI strip for the dashboard. Every value is canonical:
 *  - Total Fleet   real fleet size
 *  - Active Now    real ACTIVE display-status count, or "—" when not live
 *  - Fleet Health  mean of real vehicle health scores, or "—" when unknown
 *  - Open Alerts   canonical active alert count (critical / high breakdown)
 *
 * Open Alerts is never green at zero — a zero count is neutral, not a claim
 * of a healthy fleet. Each card navigates to its owning surface.
 */
export const DashboardKpiStrip = memo(function DashboardKpiStrip() {
  const { totalFleet, activeNow, fleetHealthScore, openAlerts, connState } = useDashboard();
  const navigate = useNavigate();

  const healthCategory = fleetHealthScore == null ? null : canonicalHealthCategory(fleetHealthScore, null);
  const healthCatLabel = healthCategory ? healthLabel(healthCategory) : 'Unavailable';

  const cards = [
    {
      key: 'fleet',
      label: 'Total Fleet',
      value: totalFleet,
      sub: `${totalFleet === 1 ? 'vehicle' : 'vehicles'} tracked`,
      color: 'var(--color-accent)',
      dot: 'var(--color-accent)',
      href: '/fleet',
      icon: <Truck size={14} />,
    },
    {
      key: 'active',
      label: 'Active Now',
      value: activeNow == null ? '\u2014' : activeNow,
      sub: activeNow == null ? 'No live data' : `${activeNow === 1 ? 'vehicle' : 'vehicles'} in motion`,
      color: connState === 'live' ? 'var(--color-green)' : 'var(--color-text-muted)',
      dot: connState === 'live' ? 'var(--color-green)' : 'var(--color-text-muted)',
      href: '/fleet',
      icon: <Activity size={14} />,
    },
    {
      key: 'health',
      label: 'Fleet Health',
      value: fleetHealthScore == null ? '\u2014' : fleetHealthScore,
      sub: healthCatLabel,
      color: healthCategory ? healthColor(healthCategory) : 'var(--color-text-muted)',
      dot: healthCategory ? healthColor(healthCategory) : 'var(--color-text-muted)',
      href: '/vehicle-health',
      icon: <HeartPulse size={14} />,
    },
    {
      key: 'alerts',
      label: 'Open Alerts',
      value: openAlerts.active,
      sub: `${openAlerts.critical} critical \u00B7 ${openAlerts.high} high`,
      color: openAlerts.active > 0 ? 'var(--color-red)' : 'var(--color-accent)',
      dot: openAlerts.active > 0 ? 'var(--color-red)' : 'var(--color-accent)',
      href: '/alerts',
      icon: <AlertTriangle size={14} />,
    },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(148px, 1fr))', gap: 10 }}>
      {cards.map((card) => (
        <button
          key={card.key}
          onClick={() => navigate(card.href)}
          aria-label={`View ${card.label} on the ${card.label} page`}
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
            padding: '12px 14px',
            borderRadius: 12,
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            cursor: 'pointer',
            textAlign: 'left',
            fontFamily: 'inherit',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = card.color;
            e.currentTarget.style.background = 'var(--color-surface-hover)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-border)';
            e.currentTarget.style.background = 'var(--color-surface)';
          }}
        >
          <span
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--color-text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: card.dot, flexShrink: 0 }} />
            {card.label}
          </span>
          <span
            style={{
              display: 'flex',
              alignItems: 'baseline',
              gap: 6,
              fontSize: 26,
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              fontVariantNumeric: 'tabular-nums',
              lineHeight: 1,
            }}
          >
            {card.value}
            <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--color-text-muted)', marginLeft: 'auto' }}>
              {card.icon}
            </span>
          </span>
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)', lineHeight: 1.2 }}>
            {card.sub}
          </span>
        </button>
      ))}
    </div>
  );
});

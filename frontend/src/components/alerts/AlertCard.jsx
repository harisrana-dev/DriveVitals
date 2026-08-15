import { memo } from 'react';
import { AlertTriangle, Bell, Info } from 'lucide-react';
import { SeverityBadge } from './SeverityBadge';
import { AlertStatusBadge } from './AlertStatusBadge';
import { severityColor, severityBg } from '../../utils/alerts';
import { useRelativeTime } from '../../hooks/useRelativeTime';

const SEV_ICONS = {
  critical: <AlertTriangle size={14} strokeWidth={2} />,
  high: <AlertTriangle size={14} strokeWidth={2} />,
  medium: <Bell size={14} strokeWidth={2} />,
  low: <Bell size={14} strokeWidth={2} />,
  info: <Info size={14} strokeWidth={2} />,
};

export const AlertCard = memo(function AlertCard({ alert, onClick, stale }) {
  const timeAgo = useRelativeTime(alert.created_at);
  const color = severityColor(alert.severity);
  const bg = severityBg(alert.severity);

  return (
    <div
      onClick={() => onClick && onClick(alert)}
      className="fade-in"
      style={{
        background: 'var(--color-surface)',
        border: `1px solid var(--color-border)`,
        borderRadius: 12,
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
        cursor: onClick ? 'pointer' : 'default',
        opacity: stale ? 0.65 : 1,
        transition: 'all 0.15s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = color;
        e.currentTarget.style.boxShadow = 'var(--color-shadow-sm)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--color-border)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div
        style={{
          width: 34,
          height: 34,
          borderRadius: 8,
          background: bg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color,
          flexShrink: 0,
        }}
      >
        {SEV_ICONS[alert.severity] || SEV_ICONS.info}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {alert.vehicle_name || alert.vehicle_id}
          </span>
          <SeverityBadge severity={alert.severity} size="sm" />
          <AlertStatusBadge status={alert.status} size="sm" />
          {stale && (
            <span
              style={{
                fontSize: 9,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--color-text-muted)',
              }}
            >
              Stale
            </span>
          )}
        </div>
        <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 2 }}>
          {alert.title}
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          {alert.driver_name ? `${alert.driver_name} · ` : ''}{alert.vehicle_id}
          {alert.created_at ? ` · ${timeAgo}` : ''}
        </div>
        {alert.message && (
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>
            {alert.message}
          </div>
        )}
      </div>
    </div>
  );
});

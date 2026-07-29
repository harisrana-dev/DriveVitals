import { memo } from 'react';
import { AlertTriangle } from 'lucide-react';
import { useAlerts } from '../../hooks/useAlerts';
import { SeverityBadge } from './SeverityBadge';
import { AlertStatusBadge } from './AlertStatusBadge';
import { useRelativeTime } from '../../hooks/useRelativeTime';

export const CriticalIncidentQueue = memo(function CriticalIncidentQueue() {
  const { incidents } = useAlerts();
  const critical = incidents.filter((a) => a.severity === 'critical');

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
        flex: 1,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 14 }}>
        <AlertTriangle size={14} style={{ color: 'var(--color-red)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Critical Incident Queue
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          {critical.length} active
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {critical.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 0' }}>
            No critical incidents.
          </div>
        ) : (
          critical.map((alert) => (
            <CriticalRow key={alert.id} alert={alert} />
          ))
        )}
      </div>
    </div>
  );
});

function CriticalRow({ alert }) {
  const duration = useRelativeTime(alert.started_at);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '8px 10px',
        borderRadius: 8,
        background: 'var(--color-red-bg)',
        border: '1px solid var(--color-red)',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {alert.vehicle_name}
          </span>
          <SeverityBadge severity="critical" size="sm" />
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
          {alert.driver_name} · {alert.eventType}
        </div>
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
          {duration}
        </div>
        <AlertStatusBadge status={alert.status} size="sm" />
      </div>
    </div>
  );
}

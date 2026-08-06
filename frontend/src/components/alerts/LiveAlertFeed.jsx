import { memo } from 'react';
import { useAlertFilters } from '../../hooks/useAlerts';
import { AlertCard } from './AlertCard';

const LIST_HEIGHT = 360;

export const LiveAlertFeed = memo(function LiveAlertFeed({ onAlertClick }) {
  const { filteredAlerts } = useAlertFilters();

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border-light)' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Live Alert Feed
          <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)', marginLeft: 8 }}>
            {filteredAlerts.length} alerts
          </span>
        </div>
      </div>

      <div style={{ height: LIST_HEIGHT, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        {filteredAlerts.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', fontSize: 13, color: 'var(--color-text-muted)' }}>
            No alerts match the current filters.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: 12 }}>
            {filteredAlerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} onClick={onAlertClick} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

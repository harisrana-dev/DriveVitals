import { memo } from 'react';
import { useAlertFilters } from '../../hooks/useAlerts';
import { AlertCard } from './AlertCard';

export const LiveAlertFeed = memo(function LiveAlertFeed({ onAlertClick }) {
  const { filteredAlerts } = useAlertFilters();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          marginBottom: 4,
        }}
      >
        Live Alert Feed
        <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)', marginLeft: 8 }}>
          {filteredAlerts.length} alerts
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {filteredAlerts.length === 0 ? (
          <div
            style={{
              padding: 32,
              textAlign: 'center',
              fontSize: 13,
              color: 'var(--color-text-muted)',
              background: 'var(--color-surface)',
              borderRadius: 12,
              border: '1px solid var(--color-border)',
            }}
          >
            No alerts match the current filters.
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} onClick={onAlertClick} />
          ))
        )}
      </div>
    </div>
  );
});

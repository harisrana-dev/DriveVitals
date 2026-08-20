import { memo } from 'react';
import { HealthKpiCards } from './HealthKpiCards';
import { ConnectionBadge } from '../ui/ConnectionBadge';
import { useLiveData } from '../../context/useLiveData';
import { useRelativeTime } from '../../hooks/useRelativeTime';

export const VehicleHealthOverview = memo(function VehicleHealthOverview() {
  const { connectionStatus, lastUpdate, syncing } = useLiveData();
  const lastUpdatedIso = lastUpdate ? new Date(lastUpdate).toISOString() : null;
  const relativeTime = useRelativeTime(lastUpdatedIso);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 12,
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: 4,
            }}
          >
            Vehicle Health
          </h1>
          <p
            style={{
              fontSize: 13,
              color: 'var(--color-text-secondary)',
            }}
          >
            Monitor vehicle condition, detect risks, and prevent unexpected downtime.
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontSize: 11,
              color: 'var(--color-text-muted)',
              whiteSpace: 'nowrap',
            }}
          >
            {syncing ? 'Syncing...' : `Last updated ${relativeTime}`}
          </span>
          <ConnectionBadge status={connectionStatus} />
        </div>
      </div>

      <HealthKpiCards />
    </div>
  );
});
